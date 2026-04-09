from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import gspread
from google.oauth2.service_account import Credentials

from drinkit_stock_transfers.logger import get_logger

logger = get_logger(__name__)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]


def normalize_row(row):
    normalized = []
    for x in row:
        if isinstance(x, Decimal):
            normalized.append(float(x))
        elif isinstance(x, datetime):
            normalized.append(x.isoformat())
        else:
            normalized.append(x)
    return normalized


class GoogleSheetsClient:
    def __init__(self, service_account_path: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(service_account_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(spreadsheet_id).sheet1

    def push_rows(self, rows: list[list], headers: list[str] | None = None):
        if not rows:
            logger.info("No rows to push")
            return
        normalized_rows = [normalize_row(r) for r in rows]
        existing = self.sheet.get_all_values()
        if headers and not existing:
            self.sheet.append_row(headers, value_input_option="USER_ENTERED")
        self.sheet.append_rows(normalized_rows, value_input_option="USER_ENTERED")
        logger.info("sheets_rows_inserted", extra={"count": len(normalized_rows)})
