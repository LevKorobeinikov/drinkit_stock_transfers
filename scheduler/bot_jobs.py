from aiogram import Bot
from aiogram_dialog import BgManagerFactory, StartMode

from bot.config import ADMIN_ID
from bot.dialogs.shift_dialog import ShiftSG


async def morning_prompt(bot: Bot, bg_factory: BgManagerFactory):
    bg_manager = bg_factory.bg(
        bot=bot,
        user_id=ADMIN_ID,
        chat_id=ADMIN_ID,
        load=True,
    )
    await bg_manager.start(
        ShiftSG.pick,
        data={"picked": [], "picked_text": "—"},
        mode=StartMode.RESET_STACK,
    )
