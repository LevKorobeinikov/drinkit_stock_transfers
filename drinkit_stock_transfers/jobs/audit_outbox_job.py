from __future__ import annotations

from bot.config import validate_and_get_settings
from bot.services.audit_sheet_service import AuditRow, AuditSheetService
from drinkit_stock_transfers.db.connection_pool import DBConnectionPool
from drinkit_stock_transfers.logger import get_logger
from drinkit_stock_transfers.repositories.audit_repository import (
    OUTBOX_CHANNEL_GOOGLE_SHEETS,
    AuditRepository,
    OutboxEvent,
)

logger = get_logger(__name__)
audit_repository = AuditRepository()


def _event_to_row(event: OutboxEvent) -> AuditRow:
    payload = event.payload
    return AuditRow(
        date=payload["date"],
        auditor=payload["auditor"],
        point=payload["point"],
        shift_team=payload["shift_team"],
        block_scores=payload["block_scores"],
        final_comment=payload["final_comment"],
        total_score=payload["total_score"],
    )


def run_audit_outbox_job(batch_size: int = 100) -> None:
    settings = validate_and_get_settings()
    DBConnectionPool.initialize(minconn=1, maxconn=5)
    try:
        events = audit_repository.claim_pending_outbox_events(limit=batch_size)
        if not events:
            return
        sheets_events = [e for e in events if e.channel == OUTBOX_CHANNEL_GOOGLE_SHEETS]
        if not sheets_events:
            return
        sheet_service = AuditSheetService(
            spreadsheet_id=settings.audit_sheet_id,
            worksheet_name=settings.audit_sheet_worksheet,
            service_account_json=settings.google_service_account_json,
        )
        try:
            sheet_service.append_rows([_event_to_row(e) for e in sheets_events])
            audit_repository.mark_outbox_events_sent([e.id for e in sheets_events])
            logger.info("Sent %s audit outbox events to Google Sheets", len(sheets_events))
        except Exception as error:
            for event in sheets_events:
                audit_repository.mark_outbox_event_failed(
                    event_id=event.id,
                    error_message=str(error),
                    backoff_seconds=30,
                )
            logger.exception("Failed to send audit outbox batch")
    except Exception as error:
        logger.exception(f"Unexpected error in audit outbox job / {error}")
