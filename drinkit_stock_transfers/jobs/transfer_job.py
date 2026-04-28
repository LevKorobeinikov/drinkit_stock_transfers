import os
from datetime import datetime, timedelta

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
    today = datetime.now().date()
    date_from = datetime.combine(today, datetime.min.time())
    date_to = date_from + timedelta(days=1)
    try:
        api_client = DodoAPIClient()
        with get_db_connection() as conn:
            repo = TransferRepository(conn)
            service = TransferService(api_client, repo)
            service.run_daily_sync()
            summary_rows = repo.fetch_zero_summary(date_from, date_to)
            if not summary_rows:
                logger.info("No data to push")
                return
            sheets_client = GoogleSheetsClient(
                service_account_path=f"/app/{os.getenv('GOOGLE_SHEETS_CLIENT_SECRET_PATH')}",
                spreadsheet_id=os.getenv("GOOGLE_SHEET_ID"),
            )
            reporting_service = ReportingService(sheets_client)
            reporting_service.push_zero_summary(summary_rows)
            logger.info(f"Pushed summary rows: {len(summary_rows)}")
    except Exception as error:
        logger.error(f"Job failed: {error}")
        raise
    finally:
        DBConnectionPool.close_all()
