import logging
import time

logger = logging.getLogger(__name__)


class RetryService:
    def __init__(self, retries=3, backoff=2):
        self.retries = retries
        self.backoff = backoff

    def call(self, func, *args, **kwargs):
        last_exception = None
        for attempt in range(1, self.retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                last_exception = error
                logger.warning(f"Attempt {attempt} failed: {error}")
                time.sleep(self.backoff * attempt)
        logger.error(f"All {self.retries} retries failed")
        raise last_exception
