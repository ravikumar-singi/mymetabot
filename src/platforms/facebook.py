"""
Facebook Graph API client for Pages.

Supports:
  - Text-only posts
  - Photo posts (media_url = public image URL)
  - Video posts (media_url = public video URL)
  - Link posts  (extra.link_url)

Meta Graph API docs: https://developers.facebook.com/docs/pages/
"""
import requests

from src.config import config
from src.database.models import ContentPost
from src.logger import get_logger
from src.platforms.base import BasePlatform

log = get_logger(__name__)


class FacebookClient(BasePlatform):
    BASE = config.GRAPH_API_BASE

    def __init__(self):
        self.page_id = config.FACEBOOK_PAGE_ID
        self.token = config.FACEBOOK_ACCESS_TOKEN

    def validate_credentials(self) -> bool:
        if not self.page_id or not self.token:
            log.warning("Facebook credentials not configured.")
            return False
        url = f"{self.BASE}/{self.page_id}"
        r = requests.get(url, params={"access_token": self.token, "fields": "id,name"})
        if r.ok:
            log.info(f"Facebook page verified: {r.json()}")
            return True
        log.error(f"Facebook credential check failed: {r.text}")
        return False

    def _build_message(self, content: ContentPost) -> str:
        parts = [content.caption or ""]
        if content.hashtags:
            parts.append(content.hashtags)
        return "\n\n".join(p for p in parts if p)

    def post(self, content: ContentPost) -> str:
        extra = content.extra or {}
        message = self._build_message(content)

        # Video post
        if content.media_url and any(
            content.media_url.lower().endswith(ext) for ext in [".mp4", ".mov", ".avi"]
        ):
            return self._post_video(content.media_url, message, content.title)

        # Photo post
        if content.media_url:
            return self._post_photo(content.media_url, message)

        # Link post
        if extra.get("link_url"):
            return self._post_link(message, extra["link_url"])

        # Text-only
        return self._post_text(message)

    def _post_text(self, message: str) -> str:
        url = f"{self.BASE}/{self.page_id}/feed"
        r = requests.post(url, data={"message": message, "access_token": self.token})
        r.raise_for_status()
        post_id = r.json()["id"]
        log.info(f"Facebook text post published: {post_id}")
        return post_id

    def _post_photo(self, photo_url: str, message: str) -> str:
        url = f"{self.BASE}/{self.page_id}/photos"
        r = requests.post(url, data={
            "url": photo_url,
            "caption": message,
            "access_token": self.token,
        })
        r.raise_for_status()
        post_id = r.json().get("post_id") or r.json().get("id")
        log.info(f"Facebook photo post published: {post_id}")
        return post_id

    def _post_video(self, video_url: str, description: str, title: str = "") -> str:
        url = f"{self.BASE}/{self.page_id}/videos"
        r = requests.post(url, data={
            "file_url": video_url,
            "description": description,
            "title": title or "",
            "access_token": self.token,
        })
        r.raise_for_status()
        post_id = r.json()["id"]
        log.info(f"Facebook video post published: {post_id}")
        return post_id

    def _post_link(self, message: str, link_url: str) -> str:
        url = f"{self.BASE}/{self.page_id}/feed"
        r = requests.post(url, data={
            "message": message,
            "link": link_url,
            "access_token": self.token,
        })
        r.raise_for_status()
        post_id = r.json()["id"]
        log.info(f"Facebook link post published: {post_id}")
        return post_id
