"""Tests for platform API clients (mocks HTTP calls)."""
import pytest
from unittest.mock import MagicMock, patch

from src.database.models import ContentPost, Platform, PostStatus


def _make_post(platform: Platform, **kwargs) -> ContentPost:
    defaults = {
        "platform": platform,
        "topic": "Test Topic",
        "caption": "Test caption with great content!",
        "hashtags": "#test #content #social",
        "status": PostStatus.DRAFT,
        "media_url": "https://example.com/image.jpg",
    }
    defaults.update(kwargs)
    return ContentPost(**defaults)


class TestInstagramClient:
    @patch("src.platforms.instagram.requests.post")
    def test_post_image(self, mock_post):
        container_resp = MagicMock()
        container_resp.json.return_value = {"id": "container_123"}
        container_resp.raise_for_status = MagicMock()

        publish_resp = MagicMock()
        publish_resp.json.return_value = {"id": "post_456"}
        publish_resp.raise_for_status = MagicMock()

        mock_post.side_effect = [container_resp, publish_resp]

        import os
        os.environ["INSTAGRAM_ACCOUNT_ID"] = "acct_123"
        os.environ["INSTAGRAM_ACCESS_TOKEN"] = "token_abc"

        from src.platforms.instagram import InstagramClient
        client = InstagramClient()
        post = _make_post(Platform.INSTAGRAM)
        post_id = client.post(post)
        assert post_id == "post_456"
        assert mock_post.call_count == 2

    def test_post_no_media_raises(self):
        import os
        os.environ["INSTAGRAM_ACCOUNT_ID"] = "acct_123"
        os.environ["INSTAGRAM_ACCESS_TOKEN"] = "token_abc"

        from src.platforms.instagram import InstagramClient
        client = InstagramClient()
        post = _make_post(Platform.INSTAGRAM, media_url=None)
        with pytest.raises(ValueError, match="media_url"):
            client.post(post)


class TestFacebookClient:
    @patch("src.platforms.facebook.requests.post")
    def test_post_text_only(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {"id": "page_123_post_789"}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        import os
        os.environ["FACEBOOK_PAGE_ID"] = "page_123"
        os.environ["FACEBOOK_ACCESS_TOKEN"] = "token_xyz"

        from src.platforms.facebook import FacebookClient
        client = FacebookClient()
        post = _make_post(Platform.FACEBOOK, media_url=None)
        post_id = client.post(post)
        assert post_id == "page_123_post_789"

    @patch("src.platforms.facebook.requests.post")
    def test_post_with_photo(self, mock_post):
        resp = MagicMock()
        resp.json.return_value = {"post_id": "photo_post_001"}
        resp.raise_for_status = MagicMock()
        mock_post.return_value = resp

        import os
        os.environ["FACEBOOK_PAGE_ID"] = "page_123"
        os.environ["FACEBOOK_ACCESS_TOKEN"] = "token_xyz"

        from src.platforms.facebook import FacebookClient
        client = FacebookClient()
        post = _make_post(Platform.FACEBOOK)
        post_id = client.post(post)
        assert post_id == "photo_post_001"


class TestDatabaseModels:
    def test_content_post_repr(self):
        post = ContentPost(platform=Platform.INSTAGRAM, status=PostStatus.DRAFT)
        assert "instagram" in repr(post)
        assert "draft" in repr(post)
