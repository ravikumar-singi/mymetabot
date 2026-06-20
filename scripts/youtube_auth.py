#!/usr/bin/env python3
"""
Run this once to authenticate with YouTube OAuth2.
It will open a browser, ask you to log in with Google, and save credentials.

Usage:
    python scripts/youtube_auth.py
"""
import sys
import pickle
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import config

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    secrets = Path(config.YOUTUBE_CLIENT_SECRETS_FILE)
    if not secrets.exists():
        print(f"ERROR: {secrets} not found.")
        print("Download OAuth2 credentials from:")
        print("  https://console.cloud.google.com/apis/credentials")
        print("Choose 'Desktop app', download JSON, and save as client_secrets.json")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    creds = flow.run_local_server(port=0)

    token_file = Path(config.YOUTUBE_TOKEN_FILE)
    with open(token_file, "wb") as f:
        pickle.dump(creds, f)

    print(f"\nSuccess! Token saved to: {token_file}")

    svc = build("youtube", "v3", credentials=creds)
    channel = svc.channels().list(part="snippet", mine=True).execute()
    if channel.get("items"):
        name = channel["items"][0]["snippet"]["title"]
        print(f"Authenticated as YouTube channel: {name}")


if __name__ == "__main__":
    main()
