from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from psycopg2.extras import execute_values

from drinkit_stock_transfers.db.connection_pool import get_db_connection


@dataclass
class AuditBlockResult:
    block_index: int
    block_title: str
    achieved: int
    max_score: int
    percent: float
    comment: str


@dataclass
class AuditRecord:
    audit_uid: str
    audited_at: datetime
    auditor: str
    point: str
    shift_team: str
    total_score: str
    final_comment: str
    block_results: list[AuditBlockResult]
    sheets_payload: dict


@dataclass
class AuditSaveResult:
    audit_id: int
    created: bool


class OutboxStatus(StrEnum):
    pending = "pending"
    processing = "processing"
    sent = "sent"
    failed = "failed"


@dataclass
class OutboxEvent:
    id: int
    audit_id: int
    channel: str
    payload: dict


OUTBOX_CHANNEL_GOOGLE_SHEETS = "google_sheets"


class AuditRepository:
    _schema_initialized = False

    def _ensure_schema(self) -> None:
        if self.__class__._schema_initialized:
            return
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    ALTER TABLE audits
                    ADD COLUMN IF NOT EXISTS audit_uid UUID
                    """
                )
                cur.execute(
                    """
                    ALTER TABLE audits
                    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW()
                    """
                )
                cur.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_audits_audit_uid
                    ON audits(audit_uid)
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS audit_outbox_events (
                        id BIGSERIAL PRIMARY KEY,
                        audit_id BIGINT NOT NULL REFERENCES audits(id) ON DELETE CASCADE,
                        channel TEXT NOT NULL,
                        payload JSONB NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        attempts INT NOT NULL DEFAULT 0,
                        next_attempt_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        sent_at TIMESTAMP NULL,
                        error_message TEXT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),
                        CONSTRAINT audit_outbox_events_unique UNIQUE (audit_id, channel)
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_audit_outbox_status_next_attempt
                    ON audit_outbox_events(status, next_attempt_at)
                    """
                )
            conn.commit()
        self.__class__._schema_initialized = True

    def save(self, record: AuditRecord) -> AuditSaveResult:
        self._ensure_schema()
        with get_db_connection() as conn:
            conn.autocommit = False
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO audits (
                            audit_uid,
                            audited_at,
                            auditor,
                            point,
                            shift_team,
                            total_score,
                            final_comment
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (audit_uid)
                        DO UPDATE SET
                            audited_at = EXCLUDED.audited_at,
                            auditor = EXCLUDED.auditor,
                            point = EXCLUDED.point,
                            shift_team = EXCLUDED.shift_team,
                            total_score = EXCLUDED.total_score,
                            final_comment = EXCLUDED.final_comment
                        RETURNING id, (xmax = 0) AS inserted
                        """,
                        (
                            record.audit_uid,
                            record.audited_at,
                            record.auditor,
                            record.point,
                            record.shift_team,
                            record.total_score,
                            record.final_comment,
                        ),
                    )
                    audit_id, inserted = cur.fetchone()

                    cur.execute("DELETE FROM audit_block_scores WHERE audit_id = %s", (audit_id,))
                    execute_values(
                        cur,
                        """
                        INSERT INTO audit_block_scores
                            (
                            audit_id, block_index, block_title, achieved,
                            max_score, percent, comment
                            )
                        VALUES %s
                        """,
                        [
                            (
                                audit_id,
                                b.block_index,
                                b.block_title,
                                b.achieved,
                                b.max_score,
                                b.percent,
                                b.comment,
                            )
                            for b in record.block_results
                        ],
                    )

                    cur.execute(
                        """
                        INSERT INTO audit_outbox_events (
                            audit_id,
                            channel,
                            payload,
                            status,
                            attempts,
                            next_attempt_at
                        )
                        VALUES (%s, %s, %s::jsonb, %s, 0, NOW())
                        ON CONFLICT (audit_id, channel)
                        DO UPDATE SET
                            payload = EXCLUDED.payload,
                            status = %s,
                            attempts = 0,
                            error_message = NULL,
                            next_attempt_at = NOW()
                        """,
                        (
                            audit_id,
                            OUTBOX_CHANNEL_GOOGLE_SHEETS,
                            json.dumps(record.sheets_payload, ensure_ascii=False),
                            OutboxStatus.pending.value,
                            OutboxStatus.pending.value,
                        ),
                    )

                conn.commit()
                return AuditSaveResult(audit_id=audit_id, created=bool(inserted))
            except Exception:
                conn.rollback()
                raise

    def claim_pending_outbox_events(self, limit: int = 100) -> list[OutboxEvent]:
        self._ensure_schema()
        with get_db_connection() as conn:
            conn.autocommit = False
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, audit_id, channel, payload
                        FROM audit_outbox_events
                        WHERE status IN (%s, %s)
                          AND next_attempt_at <= NOW()
                        ORDER BY id
                        FOR UPDATE SKIP LOCKED
                        LIMIT %s
                        """,
                        (
                            OutboxStatus.pending.value,
                            OutboxStatus.failed.value,
                            limit,
                        ),
                    )
                    rows = cur.fetchall()
                    if not rows:
                        conn.commit()
                        return []

                    ids = [row[0] for row in rows]
                    cur.execute(
                        """
                        UPDATE audit_outbox_events
                        SET status = %s, updated_at = NOW()
                        WHERE id = ANY(%s)
                        """,
                        (OutboxStatus.processing.value, ids),
                    )

                conn.commit()
                return [
                    OutboxEvent(
                        id=row[0],
                        audit_id=row[1],
                        channel=row[2],
                        payload=row[3],
                    )
                    for row in rows
                ]
            except Exception:
                conn.rollback()
                raise

    def mark_outbox_events_sent(self, event_ids: list[int]) -> None:
        self._ensure_schema()
        if not event_ids:
            return
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE audit_outbox_events
                    SET status = %s, updated_at = NOW(), sent_at = NOW(), error_message = NULL
                    WHERE id = ANY(%s)
                    """,
                    (OutboxStatus.sent.value, event_ids),
                )
            conn.commit()

    def mark_outbox_event_failed(
        self, event_id: int, error_message: str, backoff_seconds: int
    ) -> None:
        self._ensure_schema()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE audit_outbox_events
                    SET
                        status = %s,
                        attempts = attempts + 1,
                        error_message = %s,
                        next_attempt_at = NOW() + (%s || ' seconds')::interval,
                        updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        OutboxStatus.failed.value,
                        error_message[:1000],
                        backoff_seconds,
                        event_id,
                    ),
                )
            conn.commit()
