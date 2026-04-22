from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject


class AdminOnlyMiddleware(BaseMiddleware):
    def __init__(self, admin_ids: set[int] | frozenset[int]) -> None:
        self.admin_ids = set(admin_ids)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not self.admin_ids:
            return await handler(event, data)
        if self._extract_user_id(event) in self.admin_ids:
            return await handler(event, data)
        if isinstance(event, Message):
            await event.answer("Доступ только для администратора.")
            return None
        if isinstance(event, CallbackQuery):
            await event.answer("Доступ только для администратора.", show_alert=True)
            return None
        return None

    @staticmethod
    def _extract_user_id(event: TelegramObject) -> int | None:
        if isinstance(event, Message) and event.from_user:
            return event.from_user.id
        if isinstance(event, CallbackQuery) and event.from_user:
            return event.from_user.id
        return None
