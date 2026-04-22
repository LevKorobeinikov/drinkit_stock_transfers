from aiogram import Bot
from aiogram_dialog import BgManagerFactory, StartMode

from bot.config import validate_and_get_settings
from bot.dialogs.shift_dialog import ShiftSG


async def morning_prompt(bot: Bot, bg_factory: BgManagerFactory):
    settings = validate_and_get_settings()
    target_admin_id = sorted(settings.admin_ids)[0]
    bg_manager = bg_factory.bg(
        bot=bot,
        user_id=target_admin_id,
        chat_id=target_admin_id,
        load=True,
    )
    await bg_manager.start(
        ShiftSG.pick,
        data={"picked": [], "picked_text": "—"},
        mode=StartMode.RESET_STACK,
    )
