# mypy: disable-error-code=import-untyped

from __future__ import annotations

import datetime
import threading

import requests as http

from drinkit_stock_transfers.config import CLIENT_ID, CLIENT_SECRET

from .models import TokenData
from .storage import TokenStorage

TOKEN_URL = "https://auth.dodois.io/connect/token"


class AuthService:
    def __init__(self, storage: TokenStorage):
        self.storage = storage
        self._lock = threading.Lock()
        self._token: TokenData | None = self.storage.load()

    # -----------------------------
    # PUBLIC
    # -----------------------------
    def get_access_token(self) -> str:
        if not self._token:
            raise Exception("Run auth flow locally and provide tokens.json")
        if self._token.is_expired():
            return self._refresh_token()
        return self._token.access_token

    # -----------------------------
    # REFRESH
    # -----------------------------
    def _refresh_token(self) -> str:
        with self._lock:
            if self._token and not self._token.is_expired():
                return self._token.access_token
            current_token = self._token
            if current_token is None:
                raise Exception("Run auth flow locally and provide tokens.json")
            print("Refreshing token...")
            response = http.post(
                TOKEN_URL,
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": current_token.refresh_token,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            new_token = TokenData(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", current_token.refresh_token),
                expires_at=datetime.datetime.utcnow()
                + datetime.timedelta(seconds=data["expires_in"]),
            )
            self._token = new_token
            self.storage.save(new_token)
            return new_token.access_token
