import os
from datetime import datetime

from drinkit_stock_transfers.clients.dodo_api import DodoAPIClient
from drinkit_stock_transfers.clients.google_sheets_client import GoogleSheetsClient
from drinkit_stock_transfers.db.connection_pool import DBConnectionPool, get_db_connection
from drinkit_stock_transfers.logger import get_logger
from drinkit_stock_transfers.repositories.transfer_repository import TransferRepository
from drinkit_stock_transfers.services.reporting_service import ReportingService
from drinkit_stock_transfers.services.transfer_service import TransferService

logger = get_logger(__name__)


def run_transfer_job():
    DBConnectionPool.initialize(minconn=1, maxconn=5)
    try:
        api_client = DodoAPIClient()
        with get_db_connection() as conn:
            repo = TransferRepository(conn)
            service = TransferService(api_client, repo)
            service.run_daily_sync()
            zero_shipped_rows = repo.fetch_zero_shipped(datetime.now().date())
            if zero_shipped_rows:
                sheets_client = GoogleSheetsClient(
                    service_account_path=f"/app/{os.getenv('GOOGLE_SHEETS_CLIENT_SECRET_PATH')}",
                    spreadsheet_id=os.getenv("GOOGLE_SHEET_ID"),
                )
                reporting_service = ReportingService(sheets_client)
                reporting_service.push_zero_shipped(zero_shipped_rows)
                logger.info(f"Pushed {len(zero_shipped_rows)} rows")
            else:
                logger.info("No zero shipped found")
    finally:
        DBConnectionPool.close_all()
