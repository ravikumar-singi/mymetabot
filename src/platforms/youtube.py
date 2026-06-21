"""
YouTube Data API v3 client.

Supports:
  - Video upload (media_url = local file path or public URL)
  - Shorts (content.extra.is_shorts = True)
  - Playlist management

Setup: Run `python scripts/youtube_auth.py` once to generate youtube_token.json.
"""
import os
import json
import pickle
from pathlib import Path

import requests
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from src.config import config
from src.database.models import ContentPost
from src.logger import get_logger
from src.platforms.base import BasePlatform

log = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeClient(BasePlatform):
    def __init__(self):
        self._service = None

    def _get_credentials(self):
        token_file = Path(config.YOUTUBE_TOKEN_FILE)
        creds = None

        if token_file.exists():
            with open(token_file, "rb") as f:
                creds = pickle.load(f)

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, "wb") as f:
                    pickle.dump(creds, f)
            except Exception as exc:
                log.warning(f"Token refresh failed ({exc}); clearing credentials for re-auth.")
                creds = None  # falls through to InstalledAppFlow below

        if not creds or not creds.valid:
            secrets_file = Path(config.YOUTUBE_CLIENT_SECRETS_FILE)
            if not secrets_file.exists():
                raise FileNotFoundError(
                    f"YouTube client secrets not found at {secrets_file}. "
                    "Download from Google Cloud Console and save as client_secrets.json."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_file, "wb") as f:
                pickle.dump(creds, f)

        return creds

    def _get_service(self):
        if self._service is None:
            creds = self._get_credentials()
            self._service = build("youtube", "v3", credentials=creds)
        return self._service

    def validate_credentials(self) -> bool:
        try:
            svc = self._get_service()
            svc.channels().list(part="snippet", mine=True).execute()
            log.info("YouTube credentials valid.")
            return True
        except Exception as e:
            log.error(f"YouTube credential check failed: {e}")
            return False

    def _build_tags(self, content: ContentPost) -> list[str]:
        if content.tags:
            return [t.strip() for t in content.tags.split(",") if t.strip()]
        if content.hashtags:
            return [t.lstrip("#").strip() for t in content.hashtags.split() if t.startswith("#")]
        return []

    def _build_description(self, content: ContentPost) -> str:
        parts = [content.description or content.caption or ""]
        if content.hashtags:
            parts.append(f"\n{content.hashtags}")
        parts.append(
            f"\n\n─────────────────────────\n"
            f"Subscribe for more {config.BOT_NICHE} content!\n"
            f"🔔 Turn on notifications so you never miss a video."
        )
        return "\n".join(p for p in parts if p)

    def post(self, content: ContentPost) -> str:
        video_path = content.media_url
        if not video_path:
            raise ValueError(
                "YouTube upload requires a video file path in content.media_url."
            )
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        extra = content.extra or {}
        is_shorts = extra.get("is_shorts", False)
        category_id = extra.get("category_id", "22")  # 22 = People & Blogs

        body = {
            "snippet": {
                "title": content.title or content.topic or "Untitled",
                "description": self._build_description(content),
                "tags": self._build_tags(content),
                "categoryId": category_id,
                "defaultLanguage": "en",
            },
            "status": {
                "privacyStatus": extra.get("privacy", "public"),
                "selfDeclaredMadeForKids": False,
            },
        }

        if is_shorts:
            body["snippet"]["title"] = (content.title or "")[:100]

        svc = self._get_service()
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = svc.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                log.debug(f"YouTube upload {int(status.progress() * 100)}%")

        video_id = response["id"]
        log.info(f"YouTube video uploaded: https://youtu.be/{video_id}")
        return video_id
