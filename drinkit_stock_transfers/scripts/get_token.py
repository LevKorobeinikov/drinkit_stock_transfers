import datetime
import webbrowser

import requests
from flask import Flask, request

from drinkit_stock_transfers.auth.models import TokenData
from drinkit_stock_transfers.auth.storage import TokenStorage
from drinkit_stock_transfers.config import CLIENT_ID, CLIENT_SECRET
from drinkit_stock_transfers.constants import (
    CODE_CHALLENGE,
    CODE_VERIFIER,
    REDIRECT_URL,
    SCOPES,
    TOKEN_URL,
)

app = Flask(__name__)
storage = TokenStorage()


@app.route("/")
def callback():
    code = request.args.get("code")
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code_verifier": CODE_VERIFIER,
            "scope": " ".join(SCOPES),
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URL,
            "code": code,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    token = TokenData(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(seconds=data["expires_in"]),
    )
    storage.save(token)
    return "Tokens saved. You can close this page.", 200


def run_auth_flow():
    url = (
        f"https://auth.dodois.io/connect/authorize?client_id={CLIENT_ID}"
        f"&scope={' '.join(SCOPES)}"
        f"&response_type=code"
        f"&redirect_uri={REDIRECT_URL}"
        f"&code_challenge={CODE_CHALLENGE}"
        f"&code_challenge_method=S256"
    )
    print("Open this URL:")
    print(url)
    webbrowser.open(url)


if __name__ == "__main__":
    run_auth_flow()
    app.run(host="localhost", port=5001, ssl_context="adhoc")
