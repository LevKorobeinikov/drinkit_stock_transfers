from __future__ import annotations

from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import (
    ADMIN_ID,
    AUDIT_SHEET_ID,
    AUDIT_SHEET_WORKSHEET,
    GOOGLE_SHEETS_CLIENT_SECRET_PATH,
)
from bot.services.audit_definition import AUDIT_BLOCKS
from bot.services.audit_sheet_service import AuditRow, AuditSheetService

audit_router = Router(name="audit_router")
audit_sheet_service = AuditSheetService(
    spreadsheet_id=AUDIT_SHEET_ID,
    worksheet_name=AUDIT_SHEET_WORKSHEET,
    service_account_json=GOOGLE_SHEETS_CLIENT_SECRET_PATH,
)


class AuditSG(StatesGroup):
    point = State()
    shift_team = State()
    score = State()
    block_comment = State()
    final_comment = State()


def _score_keyboard(max_score: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for value in range(0, max_score + 1):
        builder.button(text=str(value), callback_data=f"audit_score:{value}")
    builder.adjust(5)
    return builder.as_markup()


def _current_item(data: dict):
    block = AUDIT_BLOCKS[data["block_idx"]]
    item = block.items[data["item_idx"]]
    return block, item


def _format_block_result(block_idx: int, scores: dict[str, int]) -> tuple[int, int, float]:
    block = AUDIT_BLOCKS[block_idx]
    achieved = sum(scores.get(item.code, 0) for item in block.items)
    max_score = block.max_score
    percent = (achieved / max_score * 100) if max_score else 0.0
    return achieved, max_score, percent


async def _send_current_item(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    block, item = _current_item(data)
    await message.answer(
        (
            f"Блок {block.index}/5\n"
            f"{block.title}\n\n"
            f"{item.code} {item.title}\n"
            f"Оцени пункт от 0 до {item.max_score}:"
        ),
        reply_markup=_score_keyboard(item.max_score),
    )


@audit_router.message(Command("audit"))
async def cmd_audit(message: Message, state: FSMContext):
    if message.from_user and ADMIN_ID and message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await state.set_state(AuditSG.point)
    await message.answer("Старт аудита.\nНапиши название точки:")


@audit_router.message(AuditSG.point)
async def on_point(message: Message, state: FSMContext):
    point = (message.text or "").strip()
    if not point:
        await message.answer("Название точки не может быть пустым. Напиши название точки:")
        return
    await state.update_data(point=point)
    await state.set_state(AuditSG.shift_team)
    await message.answer("Кто на смене? Напиши в одном сообщении.")


@audit_router.message(AuditSG.shift_team)
async def on_shift_team(message: Message, state: FSMContext):
    shift_team = (message.text or "").strip()
    if not shift_team:
        await message.answer("Состав смены не может быть пустым. Напиши в одном сообщении.")
        return
    await state.update_data(
        shift_team=shift_team,
        block_idx=0,
        item_idx=0,
        scores={},
        block_comments={},
    )
    await state.set_state(AuditSG.score)
    await _send_current_item(message, state)


@audit_router.callback_query(AuditSG.score, F.data.startswith("audit_score:"))
async def on_score(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    block_idx = data["block_idx"]
    item_idx = data["item_idx"]
    scores = dict(data["scores"])
    block = AUDIT_BLOCKS[block_idx]
    item = block.items[item_idx]
    score = int(callback.data.split(":")[1])
    scores[item.code] = score
    await state.update_data(scores=scores)
    if item_idx + 1 < len(block.items):
        await state.update_data(item_idx=item_idx + 1)
        await callback.message.answer(f"Сохранено: {item.code} = {score}/{item.max_score}")
        await _send_current_item(callback.message, state)
        await callback.answer()
        return
    achieved, max_score, percent = _format_block_result(block_idx, scores)
    await state.set_state(AuditSG.block_comment)
    await callback.message.answer(
        (
            f"Блок {block.index} завершен: {achieved}/{max_score} "
            f"({percent:.1f}%).\n"
            "Напиши комментарий к этому блоку:"
        )
    )
    await callback.answer()


@audit_router.message(AuditSG.block_comment)
async def on_block_comment(message: Message, state: FSMContext):
    comment = (message.text or "").strip()
    if not comment:
        await message.answer("Комментарий не может быть пустым. Напиши комментарий:")
        return
    data = await state.get_data()
    block_idx = data["block_idx"]
    block_comments = dict(data["block_comments"])
    block_comments[str(block_idx)] = comment
    await state.update_data(block_comments=block_comments)
    if block_idx + 1 < len(AUDIT_BLOCKS):
        await state.update_data(block_idx=block_idx + 1, item_idx=0)
        await state.set_state(AuditSG.score)
        await _send_current_item(message, state)
        return
    await state.set_state(AuditSG.final_comment)
    await message.answer("Все 5 блоков завершены. Напиши итоговый вывод (общее впечатление):")


@audit_router.message(AuditSG.final_comment)
async def on_final_comment(message: Message, state: FSMContext):
    final_comment = (message.text or "").strip()
    if not final_comment:
        await message.answer("Итоговый вывод не может быть пустым. Напиши текст:")
        return
    data = await state.get_data()
    scores = data["scores"]
    block_comments = data["block_comments"]
    block_scores_for_sheet: list[str] = []
    total_max = 0
    total_achieved = 0
    for idx, block in enumerate(AUDIT_BLOCKS):
        achieved, max_score, percent = _format_block_result(idx, scores)
        total_max += max_score
        total_achieved += achieved
        comment = block_comments.get(str(idx), "")
        block_scores_for_sheet.append(
            f"B{block.index}: {achieved}/{max_score} ({percent:.1f}%). Комментарий: {comment}"
        )
    auditor_name = (message.from_user.full_name if message.from_user else "") or "Unknown"
    total_percent = (total_achieved / total_max * 100) if total_max else 0.0
    total_score = f"{total_achieved}/{total_max} ({total_percent:.1f}%)"
    row = AuditRow(
        date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        auditor=auditor_name,
        point=data["point"],
        shift_team=data["shift_team"],
        block_scores=block_scores_for_sheet,
        final_comment=final_comment,
        total_score=total_score,
    )
    try:
        audit_sheet_service.append_row(row)
        await message.answer(
            "Аудит завершен и сохранен в Google Sheets.\n" f"Итоговый балл: {total_score}"
        )
    except Exception as error:
        await message.answer(
            "Аудит завершен, но сохранить в Google Sheets не получилось.\n" f"Ошибка: {error}"
        )
    await state.clear()
