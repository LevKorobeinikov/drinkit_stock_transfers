import datetime
from dataclasses import dataclass


@dataclass
class TokenData:
    access_token: str
    refresh_token: str
    expires_at: datetime.datetime

    def is_expired(self, buffer_seconds: int = 120) -> bool:
        return datetime.datetime.utcnow() > self.expires_at - datetime.timedelta(
            seconds=buffer_seconds
        )
