"""Tests for the content generator (mocks Claude API)."""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.database.models import Platform, PostStatus


MOCK_INSTAGRAM_RESPONSE = json.dumps({
    "caption": "Start your morning right! ☀️ Here's the secret to a productive day that nobody tells you...",
    "hashtags": "#morningroutine #productivity #lifestyle #motivation #selfcare",
    "image_prompt": "Bright minimalist bedroom at sunrise, warm golden light through sheer curtains, coffee cup on bedside table, serene and inviting atmosphere",
    "image_alt": "Person waking up in a bright, cozy bedroom at sunrise",
})

MOCK_FACEBOOK_RESPONSE = json.dumps({
    "title": "The morning habit that changed everything for me 👇",
    "caption": "Three years ago I was hitting snooze 5 times every morning. Now I wake up before my alarm — and here's exactly what changed.",
    "hashtags": "#morningroutine #productivity #lifestyle",
    "image_prompt": "Split image: before (messy bed, dark room) and after (tidy room, person energized at desk). Clean, motivational aesthetic.",
    "call_to_action": "What's YOUR morning routine secret? Drop it in the comments! 👇",
})

MOCK_YOUTUBE_RESPONSE = json.dumps({
    "title": "I Tried a 5AM Morning Routine for 30 Days — Here's What Happened",
    "description": "In this video I document my 30-day experiment waking up at 5AM...\n\n00:00 Introduction\n05:30 Week 1 struggles\n12:00 The turning point\n18:45 Final results\n\n#morningroutine #productivity",
    "tags": "morning routine, productivity, 5am club, wake up early, lifestyle",
    "hashtags": "#morningroutine #productivity #5amclub",
    "script": "[HOOK] What if waking up 2 hours earlier completely changed your life? [CONTENT] I tried the 5AM club for 30 days. Week 1 was brutal... [CTA] Follow for more life experiments!",
    "thumbnail_prompt": "Person smiling energetically at 5am, alarm clock showing 5:00, bright background, before/after split",
    "thumbnail_text": "5AM for 30 Days",
})

MOCK_TOPICS_RESPONSE = json.dumps([
    {
        "topic": "Morning Routine for Productivity",
        "pillar": "Educational / How-to",
        "hook": "The 10-minute ritual that 1000x'd my focus",
        "platforms": ["instagram", "facebook", "youtube"],
    }
])


@pytest.fixture
def mock_anthropic(monkeypatch):
    mock_client = MagicMock()
    monkeypatch.setattr("anthropic.Anthropic", lambda **kwargs: mock_client)
    return mock_client


def _make_response(text: str):
    content = MagicMock()
    content.text = text
    msg = MagicMock()
    msg.content = [content]
    return msg


@pytest.fixture
def generator(mock_anthropic, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    from src.content.generator import ContentGenerator
    gen = ContentGenerator()
    gen._client = mock_anthropic
    return gen


def test_generate_instagram_post(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = _make_response(MOCK_INSTAGRAM_RESPONSE)
    post = generator.generate_instagram_post("Morning Routine")
    assert post.platform == Platform.INSTAGRAM
    assert post.status == PostStatus.DRAFT
    assert "morning" in post.caption.lower()
    assert post.hashtags.startswith("#")
    assert post.image_prompt


def test_generate_facebook_post(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = _make_response(MOCK_FACEBOOK_RESPONSE)
    post = generator.generate_facebook_post("Morning Routine")
    assert post.platform == Platform.FACEBOOK
    assert post.title
    assert "morning" in post.caption.lower()


def test_generate_youtube_post(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = _make_response(MOCK_YOUTUBE_RESPONSE)
    post = generator.generate_youtube_post("Morning Routine")
    assert post.platform == Platform.YOUTUBE
    assert post.title
    assert post.description
    assert post.tags
    assert post.script
    assert "[HOOK]" in post.script


def test_generate_with_schedule(generator, mock_anthropic):
    from datetime import datetime
    mock_anthropic.messages.create.return_value = _make_response(MOCK_INSTAGRAM_RESPONSE)
    schedule_at = datetime(2026, 7, 1, 9, 0)
    post = generator.generate_instagram_post("Test", schedule_at=schedule_at)
    assert post.status == PostStatus.SCHEDULED
    assert post.scheduled_at == schedule_at


def test_generate_topic_ideas(generator, mock_anthropic):
    mock_anthropic.messages.create.return_value = _make_response(MOCK_TOPICS_RESPONSE)
    ideas = generator.generate_topic_ideas(count=1)
    assert isinstance(ideas, list)
    assert len(ideas) == 1
    assert ideas[0]["topic"]
    assert ideas[0]["pillar"]
