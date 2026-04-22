from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram_dialog import BgManagerFactory
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from drinkit_stock_transfers.jobs.audit_outbox_job import run_audit_outbox_job
from drinkit_stock_transfers.jobs.transfer_job import run_transfer_job
from scheduler.bot_jobs import morning_prompt


def build_scheduler(bot: Bot, bg_factory: BgManagerFactory) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Yekaterinburg"))
    scheduler.add_job(
        morning_prompt,
        trigger="cron",
        hour=11,
        minute=0,
        kwargs={"bot": bot, "bg_factory": bg_factory},
        id="bot_morning_prompt",
    )
    scheduler.add_job(
        run_transfer_job,
        trigger="cron",
        hour=15,
        minute=40,
        id="run_transfer_job",
        max_instances=1,
    )
    scheduler.add_job(
        run_audit_outbox_job,
        trigger="interval",
        seconds=30,
        id="run_audit_outbox_job",
        max_instances=1,
    )
    return scheduler
