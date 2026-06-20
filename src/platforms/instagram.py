"""
Instagram Graph API client.

Supports:
  - Photo posts  (media_url must be publicly accessible image URL)
  - Reel posts   (media_url must be publicly accessible video URL)
  - Carousel     (pass extra.media_urls list of image URLs)

Meta Graph API docs: https://developers.facebook.com/docs/instagram-api/
"""
import requests

from src.config import config
from src.database.models import ContentPost
from src.logger import get_logger
from src.platforms.base import BasePlatform

log = get_logger(__name__)


class InstagramClient(BasePlatform):
    BASE = config.GRAPH_API_BASE

    def __init__(self):
        self.account_id = config.INSTAGRAM_ACCOUNT_ID
        self.token = config.INSTAGRAM_ACCESS_TOKEN

    def validate_credentials(self) -> bool:
        if not self.account_id or not self.token:
            log.warning("Instagram credentials not configured.")
            return False
        url = f"{self.BASE}/{self.account_id}"
        r = requests.get(url, params={"access_token": self.token, "fields": "id,name"})
        if r.ok:
            log.info(f"Instagram account verified: {r.json()}")
            return True
        log.error(f"Instagram credential check failed: {r.text}")
        return False

    def _build_caption(self, content: ContentPost) -> str:
        parts = [content.caption or ""]
        if content.hashtags:
            parts.append(f"\n.\n.\n{content.hashtags}")
        return "\n".join(p for p in parts if p)

    def _create_media_container(self, media_url: str, caption: str, is_video: bool = False) -> str:
        """Step 1: Create container. Returns container ID."""
        url = f"{self.BASE}/{self.account_id}/media"
        params = {
            "access_token": self.token,
            "caption": caption,
        }
        if is_video:
            params["media_type"] = "REELS"
            params["video_url"] = media_url
        else:
            params["image_url"] = media_url

        r = requests.post(url, data=params)
        r.raise_for_status()
        container_id = r.json()["id"]
        log.debug(f"Instagram container created: {container_id}")
        return container_id

    def _publish_container(self, container_id: str) -> str:
        """Step 2: Publish the container. Returns post ID."""
        url = f"{self.BASE}/{self.account_id}/media_publish"
        r = requests.post(url, data={
            "creation_id": container_id,
            "access_token": self.token,
        })
        r.raise_for_status()
        post_id = r.json()["id"]
        log.info(f"Instagram post published: {post_id}")
        return post_id

    def _create_carousel(self, media_urls: list[str], caption: str) -> str:
        """Create a carousel post from multiple image URLs."""
        item_ids = []
        for url in media_urls:
            r = requests.post(
                f"{self.BASE}/{self.account_id}/media",
                data={
                    "image_url": url,
                    "is_carousel_item": "true",
                    "access_token": self.token,
                },
            )
            r.raise_for_status()
            item_ids.append(r.json()["id"])

        r = requests.post(
            f"{self.BASE}/{self.account_id}/media",
            data={
                "media_type": "CAROUSEL",
                "children": ",".join(item_ids),
                "caption": caption,
                "access_token": self.token,
            },
        )
        r.raise_for_status()
        carousel_id = r.json()["id"]
        return self._publish_container(carousel_id)

    def post(self, content: ContentPost) -> str:
        caption = self._build_caption(content)
        extra = content.extra or {}

        # Carousel
        if extra.get("media_urls"):
            return self._create_carousel(extra["media_urls"], caption)

        # Single image or video
        media_url = content.media_url
        if not media_url:
            raise ValueError(
                "Instagram post requires a media_url. "
                "Generate an image first and set content.media_url."
            )

        is_video = any(media_url.lower().endswith(ext) for ext in [".mp4", ".mov", ".avi"])
        container_id = self._create_media_container(media_url, caption, is_video=is_video)
        return self._publish_container(container_id)

    def post_text_only(self, content: ContentPost) -> str:
        """Post as a text-only story (uses threads-style endpoint for text)."""
        # Instagram doesn't support text-only posts via Graph API for feed.
        # This can be used for Stories with stickers or captions only.
        raise NotImplementedError(
            "Instagram requires media (image/video). "
            "Please provide a media_url or use image generation."
        )
