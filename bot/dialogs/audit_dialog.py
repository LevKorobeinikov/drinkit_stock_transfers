from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from aiogram.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Select
from aiogram_dialog.widgets.text import Const, Format

from bot.services.audit_definition import AUDIT_BLOCKS
from drinkit_stock_transfers.logger import get_logger
from drinkit_stock_transfers.repositories.audit_repository import (
    AuditBlockResult,
    AuditRecord,
    AuditRepository,
)

logger = get_logger(__name__)
audit_repository = AuditRepository()


class AuditSG(StatesGroup):
    point = State()
    shift_team = State()
    score = State()
    block_comment = State()
    final_comment = State()


@dataclass
class AuditDraft:
    audit_uid: str
    auditor_name: str
    now: datetime
    point: str
    shift_team: str
    final_comment: str
    total_score: str
    block_results: list[AuditBlockResult]
    block_scores_for_sheet: list[str]


def _current_block_and_item(data: dict):
    block = AUDIT_BLOCKS[data["block_idx"]]
    item = block.items[data["item_idx"]]
    return block, item


def _block_result(block_idx: int, scores: dict) -> tuple[int, int, float]:
    block = AUDIT_BLOCKS[block_idx]
    achieved = sum(scores.get(item.code, 0) for item in block.items)
    max_score = block.max_score
    percent = (achieved / max_score * 100) if max_score else 0.0
    return achieved, max_score, percent


def _build_block_results(
    scores: dict,
    block_comments: dict,
) -> tuple[list[AuditBlockResult], list[str], int, int]:
    block_results = []
    block_scores_for_sheet = []
    total_achieved = 0
    total_max = 0
    for idx, block in enumerate(AUDIT_BLOCKS):
        achieved, max_score, percent = _block_result(idx, scores)
        comment = block_comments.get(str(idx), "")
        total_achieved += achieved
        total_max += max_score
        block_results.append(
            AuditBlockResult(
                block_index=block.index,
                block_title=block.title,
                achieved=achieved,
                max_score=max_score,
                percent=percent,
                comment=comment,
            )
        )
        block_scores_for_sheet.append(
            f"B{block.index}: {achieved}/{max_score}" f" ({percent:.1f}%). Комментарий: {comment}"
        )
    return block_results, block_scores_for_sheet, total_achieved, total_max


def _build_sheets_payload(draft: AuditDraft) -> dict:
    return {
        "date": draft.now.strftime("%Y-%m-%d %H:%M"),
        "auditor": draft.auditor_name,
        "point": draft.point,
        "shift_team": draft.shift_team,
        "block_scores": draft.block_scores_for_sheet,
        "final_comment": draft.final_comment,
        "total_score": draft.total_score,
    }


def _save_audit(draft: AuditDraft) -> tuple[str | None, bool]:
    try:
        result = audit_repository.save(
            AuditRecord(
                audit_uid=draft.audit_uid,
                audited_at=draft.now,
                auditor=draft.auditor_name,
                point=draft.point,
                shift_team=draft.shift_team,
                total_score=draft.total_score,
                final_comment=draft.final_comment,
                block_results=draft.block_results,
                sheets_payload=_build_sheets_payload(draft),
            )
        )
        return None, result.created
    except Exception as error:
        logger.exception("Failed to save audit")
        return str(error), False


def _build_result_message(
    total_score: str,
    db_error: str | None,
    created: bool,
) -> str:
    if db_error:
        return f"Аудит не сохранен ❌\n" f"Итоговый балл: {total_score}\n" f"Ошибка: {db_error}"
    if not created:
        return (
            f"Аудит обновлен ✅\n"
            f"Итоговый балл: {total_score}\n"
            f"Поставлен в очередь отправки в Google Sheets."
        )
    return (
        f"Аудит сохранен ✅\n"
        f"Итоговый балл: {total_score}\n"
        f"Поставлен в очередь отправки в Google Sheets."
    )


async def score_getter(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.dialog_data
    block, item = _current_block_and_item(data)
    return {
        "block_index": block.index,
        "block_title": block.title,
        "item_code": item.code,
        "item_title": item.title,
        "item_max_score": item.max_score,
        "scores_buttons": [
            {"value": str(v), "label": str(v)} for v in range(0, item.max_score + 1)
        ],
    }


async def block_comment_getter(dialog_manager: DialogManager, **kwargs):
    data = dialog_manager.dialog_data
    block_idx = data["block_idx"]
    achieved, max_score, percent = _block_result(block_idx, data["scores"])
    return {
        "block_index": AUDIT_BLOCKS[block_idx].index,
        "achieved": achieved,
        "max_score": max_score,
        "percent": f"{percent:.1f}",
    }


async def on_point_entered(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    point = (message.text or "").strip()
    if not point:
        await message.answer("Название точки не может быть пустым.")
        return
    manager.dialog_data["point"] = point
    await manager.switch_to(AuditSG.shift_team)


async def on_shift_team_entered(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    shift_team = (message.text or "").strip()
    if not shift_team:
        await message.answer("Состав смены не может быть пустым.")
        return
    manager.dialog_data.update(
        {
            "audit_uid": str(uuid4()),
            "shift_team": shift_team,
            "block_idx": 0,
            "item_idx": 0,
            "scores": {},
            "block_comments": {},
        }
    )
    await manager.switch_to(AuditSG.score)


async def on_score_selected(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    data = manager.dialog_data
    block, item = _current_block_and_item(data)
    scores = dict(data["scores"])
    scores[item.code] = int(item_id)
    manager.dialog_data["scores"] = scores
    await callback.answer(f"{item.code} = {item_id}/{item.max_score}")
    if data["item_idx"] + 1 < len(block.items):
        manager.dialog_data["item_idx"] = data["item_idx"] + 1
        await manager.update({})
        return
    await manager.switch_to(AuditSG.block_comment)


async def on_block_comment_entered(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    comment = (message.text or "").strip()
    if not comment:
        await message.answer("Комментарий не может быть пустым.")
        return
    data = manager.dialog_data
    block_idx = data["block_idx"]
    block_comments = dict(data["block_comments"])
    block_comments[str(block_idx)] = comment
    manager.dialog_data["block_comments"] = block_comments
    if block_idx + 1 < len(AUDIT_BLOCKS):
        manager.dialog_data["block_idx"] = block_idx + 1
        manager.dialog_data["item_idx"] = 0
        await manager.switch_to(AuditSG.score)
        return
    await manager.switch_to(AuditSG.final_comment)


async def on_final_comment_entered(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    final_comment = (message.text or "").strip()
    if not final_comment:
        await message.answer("Итоговый вывод не может быть пустым.")
        return
    data = manager.dialog_data
    auditor_name = (message.from_user.full_name if message.from_user else "") or "Unknown"
    now = datetime.now()
    block_results, block_scores_for_sheet, total_achieved, total_max = _build_block_results(
        scores=data["scores"],
        block_comments=data["block_comments"],
    )
    total_percent = (total_achieved / total_max * 100) if total_max else 0.0
    total_score = f"{total_achieved}/{total_max} ({total_percent:.1f}%)"
    draft = AuditDraft(
        audit_uid=data["audit_uid"],
        auditor_name=auditor_name,
        now=now,
        point=data["point"],
        shift_team=data["shift_team"],
        final_comment=final_comment,
        total_score=total_score,
        block_results=block_results,
        block_scores_for_sheet=block_scores_for_sheet,
    )
    db_error, created = _save_audit(draft)
    await message.answer(_build_result_message(total_score, db_error, created))
    await manager.done()


audit_dialog = Dialog(
    Window(
        Const("Старт аудита.\nНапиши название точки:"),
        MessageInput(on_point_entered),
        state=AuditSG.point,
    ),
    Window(
        Const("Кто на смене? Напиши в одном сообщении."),
        MessageInput(on_shift_team_entered),
        Back(Const("Назад")),
        state=AuditSG.shift_team,
    ),
    Window(
        Format(
            "Блок {block_index}/5\n"
            "{block_title}\n\n"
            "{item_code} {item_title}\n"
            "Оцени от 0 до {item_max_score}:"
        ),
        Select(
            Format("{item[label]}"),
            id="score_select",
            items="scores_buttons",
            item_id_getter=lambda x: x["value"],
            on_click=on_score_selected,
        ),
        state=AuditSG.score,
        getter=score_getter,
    ),
    Window(
        Format(
            "Блок {block_index} завершен: "
            "{achieved}/{max_score} ({percent}%).\n"
            "Напиши комментарий к этому блоку:"
        ),
        MessageInput(on_block_comment_entered),
        state=AuditSG.block_comment,
        getter=block_comment_getter,
    ),
    Window(
        Const("Все 5 блоков завершены.\nНапиши итоговый вывод:"),
        MessageInput(on_final_comment_entered),
        state=AuditSG.final_comment,
    ),
)
