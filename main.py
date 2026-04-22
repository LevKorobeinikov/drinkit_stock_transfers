from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import Message
from aiogram_dialog import StartMode, setup_dialogs
from aiohttp import web
from redis.asyncio import Redis

from bot.config import validate_and_get_settings
from bot.dialogs.audit_dialog import AuditSG, audit_dialog
from bot.dialogs.employees_dialog import EmployeesSG, employees_dialog
from bot.dialogs.shift_dialog import ShiftSG, shift_dialog
from bot.middlewares.admin_only import AdminOnlyMiddleware
from scheduler.scheduler_service import build_scheduler

redis = Redis(host="redis", port=6379)


async def health(request):
    return web.Response(text="OK")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()


async def cmd_shift(message: Message, dialog_manager):
    await dialog_manager.start(
        ShiftSG.pick,
        data={"picked": []},
        mode=StartMode.RESET_STACK,
    )


async def cmd_employees(message: Message, dialog_manager):
    await dialog_manager.start(
        EmployeesSG.menu,
        mode=StartMode.RESET_STACK,
    )


async def cmd_audit(message: Message, dialog_manager):
    await dialog_manager.start(AuditSG.point, mode=StartMode.RESET_STACK)


async def main():
    settings = validate_and_get_settings()
    await start_health_server()
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(
        storage=RedisStorage(
            redis=redis,
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    )
    admin_only = AdminOnlyMiddleware(settings.admin_ids)
    dp.message.middleware(admin_only)
    dp.callback_query.middleware(admin_only)
    dp.include_router(shift_dialog)
    dp.include_router(employees_dialog)
    dp.include_router(audit_dialog)
    bg_factory = setup_dialogs(dp)
    dp.message.register(cmd_shift, Command("shift"))
    dp.message.register(cmd_employees, Command("employees"))
    dp.message.register(cmd_audit, Command("audit"))
    scheduler = build_scheduler(bot, bg_factory)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
