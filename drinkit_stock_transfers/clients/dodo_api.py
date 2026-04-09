from datetime import datetime

import requests

from drinkit_stock_transfers.auth import auth_service
from drinkit_stock_transfers.config import API_URL, UNITS
from drinkit_stock_transfers.logger import get_logger
from drinkit_stock_transfers.services.pagination import Paginator
from drinkit_stock_transfers.services.retry_service import RetryService

logger = get_logger(__name__)


class DodoAPIClient:
    def __init__(self, units: str = None):
        self.session = requests.Session()
        self.units = units or UNITS
        self.retry_service = RetryService()

    def _get_headers(self) -> dict:
        """Return up-to-date headers with access token."""
        token = auth_service.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def _fetch_page(self, skip: int, date_from: datetime, date_to: datetime, units: str) -> dict:
        """Fetch a single transfers page."""
        params = {
            "units": units,
            "receivedFrom": date_from.isoformat(),
            "receivedTo": date_to.isoformat(),
            "skip": skip,
        }

        def request_page():
            headers = self._get_headers()
            response = self.session.get(API_URL, headers=headers, params=params, timeout=10)
            if response.status_code == 401:
                logger.warning("401 Unauthorized, refreshing token...")
                headers = self._get_headers()
                response = self.session.get(API_URL, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        return self.retry_service.call(request_page)

    def fetch_transfers(self, date_from: datetime, date_to: datetime, units: str = None):
        """Fetch all transfers for a period (paginated)."""
        paginator = Paginator(
            self.session, API_URL, {"Authorization": f"Bearer {auth_service.get_access_token()}"}
        )
        params = {
            "units": units or self.units,
            "receivedFrom": date_from.isoformat(),
            "receivedTo": date_to.isoformat(),
        }
        return self.retry_service.call(paginator.fetch_all, params)
