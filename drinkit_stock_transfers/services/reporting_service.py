from typing import List

from drinkit_stock_transfers.clients.google_sheets_client import GoogleSheetsClient
from drinkit_stock_transfers.constants import HEADERS_ZERO_SHIPPED
from drinkit_stock_transfers.logger import get_logger
from drinkit_stock_transfers.services.retry_service import RetryService

logger = get_logger(__name__)


class ReportingService:
    def __init__(self, sheets_client: GoogleSheetsClient, retry_service: RetryService = None):
        self.sheets_client = sheets_client
        self.retry_service = retry_service or RetryService(retries=3, backoff=2)

    def push_zero_shipped(self, zero_shipped_rows: List[tuple]):
        if not zero_shipped_rows:
            logger.info("No zero shipped rows to push")
            return
        rows = [list(r) for r in zero_shipped_rows]
        logger.info(f"Start pushing {len(rows)} rows to Google Sheets")

        def _push():
            self.sheets_client.push_rows(rows, headers=HEADERS_ZERO_SHIPPED)

        try:
            self.retry_service.call(_push)
            logger.info(f"Successfully pushed {len(rows)} rows to Google Sheets")
        except Exception as error:
            logger.error(f"Failed to push rows to Google Sheets: {error}")
            raise
