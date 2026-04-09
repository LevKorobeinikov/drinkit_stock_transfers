from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
EMPLOYEES_FILE = os.getenv("EMPLOYEES_FILE") or "storage/employees.json"
