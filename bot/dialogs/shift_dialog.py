from __future__ import annotations

from aiogram.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Select
from aiogram_dialog.widgets.text import Const, Format

from bot.config import GROUP_CHAT_ID
from bot.services.assignment_service import (
    build_assignment,
    format_assignment,
)
from bot.services.container import employee_service


class ShiftSG(StatesGroup):
    pick = State()


# -----------------------------
# GETTER
# -----------------------------
async def shift_getter(dialog_manager: DialogManager, **kwargs):
    picked = dialog_manager.dialog_data.get("picked", [])
    employees = employee_service.list()
    items = []
    for emp in employees:
        items.append({"name": emp, "label": f"{'✓ ' if emp in picked else ''}{emp}"})
    return {
        "employees": items,
        "picked_count": len(picked),
    }


# -----------------------------
# CLICK HANDLER
# -----------------------------
async def on_employee_click(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    picked = manager.dialog_data.setdefault("picked", [])
    if item_id in picked:
        picked.remove(item_id)
    else:
        if len(picked) >= 2:
            await callback.answer("Можно выбрать только 2", show_alert=True)
            return
        picked.append(item_id)
    await manager.update({})


# -----------------------------
# DONE
# -----------------------------
async def on_done(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    picked = manager.dialog_data.get("picked", [])
    if len(picked) != 2:
        await callback.answer("Выбери ровно 2 сотрудников", show_alert=True)
        return
    assignment = build_assignment(picked)
    result = format_assignment(assignment)
    await callback.message.bot.send_message(chat_id=GROUP_CHAT_ID, text=result)
    await callback.message.answer("Отправил в группу ✅")
    manager.dialog_data.clear()
    await manager.done()


# -----------------------------
# RESET
# -----------------------------
async def on_reset(
    callback: CallbackQuery,
    button: Button,
    manager: DialogManager,
):
    manager.dialog_data["picked"] = []
    await manager.update({})


# -----------------------------
# DIALOG
# -----------------------------
shift_dialog = Dialog(
    Window(
        Const("Кто на смене? Выбери 2 сотрудников"),
        Select(
            Format("{item[label]}"),
            id="employee_select",
            items="employees",
            item_id_getter=lambda x: x["name"],
            on_click=on_employee_click,
        ),
        Format("Выбрано: {picked_count}/2"),
        Button(Const("Сформировать"), id="done", on_click=on_done),
        Button(Const("Сбросить"), id="reset", on_click=on_reset),
        state=ShiftSG.pick,
        getter=shift_getter,
    )
)
