from __future__ import annotations

import datetime
import json
import os

from .models import TokenData


class TokenStorage:
    def __init__(self, path: str = "drinkit_stock_transfers/tokens.json"):
        self.path = path

    def load(self) -> TokenData | None:
        if not os.path.exists(self.path):
            return None
        with open(self.path, "r") as f:
            data = json.load(f)
        return TokenData(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.datetime.fromisoformat(data["expires_at"]),
        )

    def save(self, token: TokenData):
        with open(self.path, "w") as f:
            json.dump(
                {
                    "access_token": token.access_token,
                    "refresh_token": token.refresh_token,
                    "expires_at": token.expires_at.isoformat(),
                },
                f,
            )
