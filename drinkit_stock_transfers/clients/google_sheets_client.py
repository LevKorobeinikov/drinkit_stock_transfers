from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import ValueInputOption

from drinkit_stock_transfers.logger import get_logger

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def normalize_row(row):
    normalized = []
    for x in row:
        if isinstance(x, Decimal):
            normalized.append(float(x))
        elif isinstance(x, datetime):
            normalized.append(x.isoformat())
        elif isinstance(x, date):
            normalized.append(x.isoformat())
        else:
            normalized.append(x)
    return normalized


class GoogleSheetsClient:
    def __init__(self, service_account_path: str, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(service_account_path, scopes=SCOPES)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        self.sheet = self.spreadsheet.sheet1  # default sheet (старый отчет)

    def push_rows(self, rows: list[list], headers: list[str] | None = None):
        if not rows:
            logger.info("No rows to push")
            return
        normalized_rows = [normalize_row(r) for r in rows]
        if headers and not self.sheet.get_all_values():
            self.sheet.append_row(headers, value_input_option=ValueInputOption.user_entered)
        self.sheet.append_rows(
            normalized_rows,
            value_input_option=ValueInputOption.user_entered,
        )
        logger.info("sheets_rows_inserted", extra={"count": len(normalized_rows)})

    def push_summary_rows(
        self,
        sheet_name: str,
        rows: list[list],
        headers: list[str],
    ):
        if not rows:
            logger.info("No summary rows to push")
            return
        worksheet = self._get_or_create_sheet(sheet_name)
        normalized_rows = [normalize_row(r) for r in rows]
        if not worksheet.get_all_values():
            worksheet.append_row(
                headers,
                value_input_option=ValueInputOption.user_entered,
            )
        worksheet.insert_rows(normalized_rows, row=2)
        logger.info("summary_rows_pushed", extra={"count": len(rows)})

    def _get_or_create_sheet(self, name: str):
        try:
            return self.spreadsheet.worksheet(name)
        except gspread.WorksheetNotFound:
            logger.info(f"Creating sheet: {name}")
            return self.spreadsheet.add_worksheet(
                title=name,
                rows="1000",
                cols="20",
            )
