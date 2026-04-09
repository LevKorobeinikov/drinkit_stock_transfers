from __future__ import annotations

from aiogram.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from bot.services.container import employee_service


class EmployeesSG(StatesGroup):
    menu = State()
    add = State()
    remove = State()


async def employees_getter(**kwargs):
    employees = employee_service.list()
    if employees:
        text = "\n".join(f"• {name}" for name in employees)
    else:
        text = "Список пуст"
    return {
        "employees": employees,
        "employees_text": text,
    }


async def on_employee_added(
    message: Message,
    message_input: MessageInput,
    manager: DialogManager,
):
    name = (message.text or "").strip()
    try:
        employee_service.add(name)
        await message.answer(f"Добавил: {name}")
        await manager.switch_to(EmployeesSG.menu)
    except Exception as error:
        await message.answer(f"Ошибка: {error}")


async def on_employee_removed(
    callback: CallbackQuery,
    widget: Select,
    manager: DialogManager,
    item_id: str,
):
    try:
        employee_service.remove(item_id)
        await callback.answer(f"Удалил: {item_id}", show_alert=False)
        await manager.switch_to(EmployeesSG.menu)
    except Exception as error:
        await callback.answer(str(error), show_alert=True)


employees_dialog = Dialog(
    Window(
        Const("Управление сотрудниками"),
        Format("{employees_text}"),
        SwitchTo(Const("Добавить"), id="to_add", state=EmployeesSG.add),
        SwitchTo(Const("Удалить"), id="to_remove", state=EmployeesSG.remove),
        Back(Const("Назад")),
        state=EmployeesSG.menu,
        getter=employees_getter,
    ),
    Window(
        Const("Напиши имя сотрудника одним сообщением."),
        MessageInput(on_employee_added),
        Back(Const("Назад")),
        state=EmployeesSG.add,
    ),
    Window(
        Const("Выбери сотрудника для удаления."),
        Select(
            Format("• {item}"),
            id="remove_employee",
            items="employees",
            item_id_getter=lambda item: item,
            on_click=on_employee_removed,
        ),
        Back(Const("Назад")),
        state=EmployeesSG.remove,
        getter=employees_getter,
    ),
)
