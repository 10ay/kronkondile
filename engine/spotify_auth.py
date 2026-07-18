"""
Spotify login
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlencode
import requests

root = Path(__file__).resolve().parent.parent
token_path = root / "data" / "spotify_token.json"
pkce_path = root / "data" / "spotify_pkce.json"

accounts_base = "https://accounts.spotify.com"
redirect_uri = "http://127.0.0.1:8888/callback"
scopes = "playlist-modify-public playlist-modify-private"
client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip() or "272c8f949f3d418295af67b394d9e8a7"


def load_tokens():
    if token_path.exists():
        return json.loads(token_path.read_text(encoding="utf-8"))
    return {}


def save_tokens(tokens):
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")


def clear_tokens():
    if token_path.exists():
        token_path.unlink()
    if pkce_path.exists():
        pkce_path.unlink()


def pkce_pair():
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def authorize_url(redirect=redirect_uri, verifier=None):
    if verifier is None:
        # CLI flow: one login at a time, keep the verifier on disk.
        verifier, challenge = pkce_pair()
        pkce_path.parent.mkdir(parents=True, exist_ok=True)
        pkce_path.write_text(json.dumps({"verifier": verifier}), encoding="utf-8")
    else:
        # Web flow: caller keeps the verifier (many users may log in at once).
        digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect,
        "scope": scopes,
        "code_challenge_method": "S256",
        "code_challenge": challenge,
        "show_dialog": "true",
    }
    return f"{accounts_base}/authorize?{urlencode(params)}"


def token_request(data):
    response = requests.post(
        f"{accounts_base}/api/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )
    response.raise_for_status()
    tokens = response.json()
    tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600))
    old = load_tokens()
    if "refresh_token" not in tokens and "refresh_token" in old:
        tokens["refresh_token"] = old["refresh_token"]
    save_tokens(tokens)
    return tokens["access_token"]


def exchange_code(code, redirect=redirect_uri, verifier=None):
    if verifier is None:
        if not pkce_path.exists():
            raise RuntimeError("Missing login state — click Save on Spotify again.")
        verifier = json.loads(pkce_path.read_text(encoding="utf-8"))["verifier"]
    token = token_request({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect,
        "client_id": client_id,
        "code_verifier": verifier,
    })
    if pkce_path.exists():
        pkce_path.unlink()
    return token
