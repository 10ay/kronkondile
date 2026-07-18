"""
Spotify login
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from pathlib import Path
from urllib.parse import urlencode
import requests

root = Path(__file__).resolve().parent.parent
client_path = root / "data" / "spotify_client.json"

accounts_base = "https://accounts.spotify.com"
redirect_uri = "http://127.0.0.1:8888/callback"
scopes = "playlist-modify-public playlist-modify-private"


def valid_client_id(cid):
    return len(cid) == 32 and all(c in "0123456789abcdefABCDEF" for c in cid)


def load_client_id():
    """The Client ID the CLI user saved last time (bring-your-own Spotify app)."""
    if client_path.exists():
        return json.loads(client_path.read_text(encoding="utf-8")).get("client_id", "")
    return ""


def save_client_id(cid):
    client_path.parent.mkdir(parents=True, exist_ok=True)
    client_path.write_text(json.dumps({"client_id": cid}), encoding="utf-8")


def new_verifier():
    return secrets.token_urlsafe(64)


def authorize_url(spotify_client_id, verifier, redirect=redirect_uri):
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    params = {
        "client_id": spotify_client_id,
        "response_type": "code",
        "redirect_uri": redirect,
        "scope": scopes,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "show_dialog": "true",
    }
    return f"{accounts_base}/authorize?{urlencode(params)}"


def exchange_code(code, spotify_client_id, verifier, redirect=redirect_uri):
    response = requests.post(
        f"{accounts_base}/api/token",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect,
            "client_id": spotify_client_id,
            "code_verifier": verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["access_token"]
