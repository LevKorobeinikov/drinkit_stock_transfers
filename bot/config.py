from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
EMPLOYEES_FILE = os.getenv("EMPLOYEES_FILE") or "storage/employees.json"

AUDIT_SHEET_ID = os.getenv("AUDIT_SHEET_ID", "")
AUDIT_SHEET_WORKSHEET = os.getenv("AUDIT_SHEET_WORKSHEET", "")
GOOGLE_SHEETS_CLIENT_SECRET_PATH = os.getenv("GOOGLE_SHEETS_CLIENT_SECRET_PATH", "")
ADMIN_IDS = os.getenv("ADMIN_IDS", "")


@dataclass(frozen=True)
class BotSettings:
    bot_token: str
    admin_ids: frozenset[int]
    audit_sheet_id: str
    audit_sheet_worksheet: str
    google_service_account_json: str


def _parse_admin_ids() -> tuple[frozenset[int], list[str]]:
    errors: list[str] = []
    result: set[int] = {8420683197, 954351510}
    if ADMIN_ID > 0:
        result.add(ADMIN_ID)
    for raw in ADMIN_IDS.split(","):
        value = raw.strip()
        if not value:
            continue
        try:
            result.add(int(value))
        except ValueError:
            errors.append(f"Invalid admin id in ADMIN_IDS: {value}")
    return frozenset(result), errors


def _read_service_account_json(path: str) -> str:
    content = Path(path).read_text(encoding="utf-8")
    json.loads(content)
    return content


def validate_and_get_settings() -> BotSettings:
    errors: list[str] = []
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN is required")
    if not AUDIT_SHEET_ID:
        errors.append("AUDIT_SHEET_ID is required")
    if not AUDIT_SHEET_WORKSHEET:
        errors.append("AUDIT_SHEET_WORKSHEET is required")
    if not GOOGLE_SHEETS_CLIENT_SECRET_PATH:
        errors.append("GOOGLE_SHEETS_CLIENT_SECRET_PATH is required")
    service_account_json = ""
    if GOOGLE_SHEETS_CLIENT_SECRET_PATH:
        try:
            service_account_json = _read_service_account_json(GOOGLE_SHEETS_CLIENT_SECRET_PATH)
        except FileNotFoundError:
            errors.append(
                f"GOOGLE_SHEETS_CLIENT_SECRET_PATH file not found: "
                f"{GOOGLE_SHEETS_CLIENT_SECRET_PATH}"
            )
        except json.JSONDecodeError:
            errors.append("GOOGLE_SHEETS_CLIENT_SECRET_PATH must point to valid JSON")

    admin_ids, admin_errors = _parse_admin_ids()
    errors.extend(admin_errors)
    if not admin_ids:
        errors.append("At least one admin id must be configured")
    if errors:
        raise RuntimeError("Configuration validation failed: " + "; ".join(errors))
    return BotSettings(
        bot_token=BOT_TOKEN or "",
        admin_ids=admin_ids,
        audit_sheet_id=AUDIT_SHEET_ID,
        audit_sheet_worksheet=AUDIT_SHEET_WORKSHEET,
        google_service_account_json=service_account_json,
    )
