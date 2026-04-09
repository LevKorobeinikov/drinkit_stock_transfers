import os

from dotenv import load_dotenv

load_dotenv()

# OAuth
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# API
API_URL = "https://api.dodois.io/drinkit/ru/accounting/stock-transfers"
UNITS = os.getenv("UNITS")

# Database
DB_PARAMS = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "db"),
    "port": os.getenv("DB_PORT", 5432),
}

# Google Sheets
GOOGLE_SHEETS_CLIENT_SECRET_PATH = os.getenv("GOOGLE_SHEETS_CLIENT_SECRET_PATH")
