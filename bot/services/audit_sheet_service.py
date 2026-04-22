from __future__ import annotations

import json
from dataclasses import dataclass

import gspread


@dataclass
class AuditRow:
    date: str
    auditor: str
    point: str
    shift_team: str
    block_scores: list[str]
    final_comment: str
    total_score: str


class AuditSheetService:
    def __init__(
        self,
        spreadsheet_id: str,
        worksheet_name: str,
        service_account_json: str,
    ) -> None:
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        self.service_account_json = service_account_json
        self._worksheet = None

    def is_configured(self) -> bool:
        return bool(self.spreadsheet_id and self.worksheet_name and self.service_account_json)

    def _build_values(self, row: AuditRow) -> list[str]:
        return [
            row.date,
            row.auditor,
            row.point,
            row.shift_team,
            *row.block_scores,
            row.total_score,
            row.final_comment,
        ]

    def _get_worksheet(self):
        if not self.is_configured():
            raise RuntimeError("Google Sheets config is missing for audit report")
        if self._worksheet is None:
            client = gspread.service_account_from_dict(json.loads(self.service_account_json))
            self._worksheet = client.open_by_key(self.spreadsheet_id).worksheet(self.worksheet_name)
        return self._worksheet

    def append_row(self, row: AuditRow) -> None:
        self._get_worksheet().append_row(
            self._build_values(row),
            value_input_option="USER_ENTERED",
        )

    def append_rows(self, rows: list[AuditRow]) -> None:
        if not rows:
            return
        self._get_worksheet().append_rows(
            [self._build_values(row) for row in rows],
            value_input_option="USER_ENTERED",
        )
