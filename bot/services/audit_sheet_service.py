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

    def is_configured(self) -> bool:
        return bool(self.spreadsheet_id and self.worksheet_name and self.service_account_json)

    def append_row(self, row: AuditRow) -> None:
        if not self.is_configured():
            raise RuntimeError("Google Sheets config is missing for audit report")
        client = gspread.service_account_from_dict(json.loads(self.service_account_json))
        worksheet = client.open_by_key(self.spreadsheet_id).worksheet(self.worksheet_name)
        worksheet.append_row(
            [
                row.date,
                row.auditor,
                row.point,
                row.shift_team,
                *row.block_scores,
                row.total_score,
                row.final_comment,
            ],
            value_input_option="USER_ENTERED",
        )
