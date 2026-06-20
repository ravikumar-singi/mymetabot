#!/usr/bin/env python3
"""
Exchange a short-lived Meta User Access Token for a long-lived one (60 days).
Run this whenever your Instagram/Facebook access token is about to expire.

Usage:
    python scripts/refresh_meta_token.py --token YOUR_SHORT_LIVED_TOKEN
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
import requests
from src.config import config


@click.command()
@click.option("--token", required=True, help="Short-lived user access token from Meta")
def main(token: str):
    """Exchange a short-lived token for a long-lived one."""
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": config.META_APP_ID,
        "client_secret": config.META_APP_SECRET,
        "fb_exchange_token": token,
    }
    r = requests.get(url, params=params)
    data = r.json()

    if "access_token" in data:
        print(f"\nLong-lived token (valid ~60 days):\n{data['access_token']}")
        print(f"\nExpires in: {data.get('expires_in', 'N/A')} seconds")
        print("\nUpdate INSTAGRAM_ACCESS_TOKEN and FACEBOOK_ACCESS_TOKEN in your .env file.")
    else:
        print(f"Error: {data}")
        sys.exit(1)


if __name__ == "__main__":
    main()
