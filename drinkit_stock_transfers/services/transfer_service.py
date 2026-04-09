from datetime import datetime, timedelta

from drinkit_stock_transfers.logger import get_logger

logger = get_logger(__name__)


class TransferService:
    def __init__(self, api_client, repository):
        self.api_client = api_client
        self.repository = repository

    def run_daily_sync(self):
        today = datetime.now().date()
        date_from = datetime.combine(today, datetime.min.time())
        date_to = datetime.combine(today + timedelta(days=1), datetime.min.time())
        logger.info(f"Sync transfers from {date_from} to {date_to}")
        transfers = self.api_client.fetch_transfers(date_from, date_to)
        if not transfers:
            logger.info("No transfers received")
            return
        self.repository.save_transfers(transfers)
