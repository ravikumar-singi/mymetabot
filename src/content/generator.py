import json
import re
from datetime import datetime, timedelta
from typing import Optional

import anthropic

from src.config import config
from src.database.models import ContentPost, Platform, PostStatus
from src.content.templates import (
    PLATFORM_SPECS,
    SYSTEM_PROMPT_TEMPLATE,
    INSTAGRAM_PROMPT,
    FACEBOOK_PROMPT,
    YOUTUBE_PROMPT,
    TOPIC_IDEAS_PROMPT,
)
from src.logger import get_logger

log = get_logger(__name__)


class ContentGenerator:
    MODEL = "claude-sonnet-4-6"

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set.")
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def _system_prompt(self) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            brand_name=config.BOT_BRAND_NAME,
            niche=config.BOT_NICHE,
            target_audience=config.BOT_TARGET_AUDIENCE,
            tone=config.BOT_TONE,
        )

    def _call_claude(self, user_prompt: str, max_tokens: int = 1500) -> str:
        response = self._client.messages.create(
            model=self.MODEL,
            max_tokens=max_tokens,
            system=self._system_prompt(),
            messages=[{"role": "user", "content": user_prompt}],
        )
        if not response.content:
            raise ValueError(
                f"Claude returned empty response (stop_reason={response.stop_reason})"
            )
        return response.content[0].text

    def _parse_json(self, raw: str) -> dict:
        """Extract and parse JSON from Claude's response."""
        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            raise ValueError(f"No JSON found in response:\n{raw[:200]}")
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed JSON in Claude response: {exc}\nRaw: {raw[:200]}"
            ) from exc

    def _parse_json_array(self, raw: str) -> list:
        match = re.search(r"\[[\s\S]*\]", raw)
        if not match:
            raise ValueError(f"No JSON array found in response:\n{raw[:200]}")
        try:
            return json.loads(match.group())
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Malformed JSON array in Claude response: {exc}\nRaw: {raw[:200]}"
            ) from exc

    def generate_instagram_post(self, topic: str, schedule_at: Optional[datetime] = None) -> ContentPost:
        log.info(f"Generating Instagram post for topic: {topic}")
        spec = PLATFORM_SPECS[Platform.INSTAGRAM]
        prompt = INSTAGRAM_PROMPT.format(
            topic=topic,
            length=spec.optimal_post_length,
            hashtags=spec.hashtag_count,
        )
        raw = self._call_claude(prompt)
        data = self._parse_json(raw)

        post = ContentPost(
            platform=Platform.INSTAGRAM,
            topic=topic,
            niche=config.BOT_NICHE,
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", ""),
            image_prompt=data.get("image_prompt", ""),
            extra={"image_alt": data.get("image_alt", "")},
            status=PostStatus.SCHEDULED if schedule_at else PostStatus.DRAFT,
            scheduled_at=schedule_at,
        )
        log.info("Instagram post generated.")
        return post

    def generate_facebook_post(self, topic: str, schedule_at: Optional[datetime] = None) -> ContentPost:
        log.info(f"Generating Facebook post for topic: {topic}")
        spec = PLATFORM_SPECS[Platform.FACEBOOK]
        prompt = FACEBOOK_PROMPT.format(
            topic=topic,
            length=spec.optimal_post_length,
            hashtags=spec.hashtag_count,
        )
        raw = self._call_claude(prompt)
        data = self._parse_json(raw)

        cta = data.get("call_to_action", "")
        caption_parts = [data.get("title", ""), data.get("caption", ""), cta]
        full_caption = "\n\n".join(p for p in caption_parts if p)

        post = ContentPost(
            platform=Platform.FACEBOOK,
            topic=topic,
            niche=config.BOT_NICHE,
            title=data.get("title", ""),
            caption=full_caption,
            hashtags=data.get("hashtags", ""),
            image_prompt=data.get("image_prompt", ""),
            extra={"call_to_action": cta},
            status=PostStatus.SCHEDULED if schedule_at else PostStatus.DRAFT,
            scheduled_at=schedule_at,
        )
        log.info("Facebook post generated.")
        return post

    def generate_youtube_post(self, topic: str, schedule_at: Optional[datetime] = None) -> ContentPost:
        log.info(f"Generating YouTube content for topic: {topic}")
        spec = PLATFORM_SPECS[Platform.YOUTUBE]
        prompt = YOUTUBE_PROMPT.format(
            topic=topic,
            length=spec.optimal_post_length,
            hashtags=spec.hashtag_count,
        )
        raw = self._call_claude(prompt, max_tokens=2500)
        data = self._parse_json(raw)

        post = ContentPost(
            platform=Platform.YOUTUBE,
            topic=topic,
            niche=config.BOT_NICHE,
            title=data.get("title", ""),
            description=data.get("description", ""),
            hashtags=data.get("hashtags", ""),
            tags=data.get("tags", ""),
            script=data.get("script", ""),
            image_prompt=data.get("thumbnail_prompt", ""),
            extra={
                "thumbnail_text": data.get("thumbnail_text", ""),
            },
            status=PostStatus.SCHEDULED if schedule_at else PostStatus.DRAFT,
            scheduled_at=schedule_at,
        )
        log.info("YouTube content generated.")
        return post

    def generate_topic_ideas(self, count: int = 10) -> list[dict]:
        log.info(f"Generating {count} topic ideas for niche: {config.BOT_NICHE}")
        prompt = TOPIC_IDEAS_PROMPT.format(
            count=count,
            niche=config.BOT_NICHE,
            audience=config.BOT_TARGET_AUDIENCE,
        )
        raw = self._call_claude(prompt, max_tokens=3000)
        ideas = self._parse_json_array(raw)
        log.info(f"Generated {len(ideas)} topic ideas.")
        return ideas

    def generate_content_calendar(
        self,
        weeks: int = 2,
        posts_per_week_per_platform: int = 3,
    ) -> list[ContentPost]:
        """Generate a full content calendar and return unsaved ContentPost objects."""
        ideas = self.generate_topic_ideas(count=weeks * posts_per_week_per_platform * 3)
        posts: list[ContentPost] = []
        now = datetime.utcnow()
        idea_idx = 0

        for week in range(weeks):
            week_start = now + timedelta(weeks=week)
            post_days = [0, 2, 4]  # Mon, Wed, Fri (0-indexed from week_start)

            for day_offset in post_days[:posts_per_week_per_platform]:
                post_date = week_start + timedelta(days=day_offset)

                for platform, hour in [
                    (Platform.INSTAGRAM, 9),
                    (Platform.FACEBOOK, 10),
                    (Platform.YOUTUBE, 14),
                ]:
                    if idea_idx >= len(ideas):
                        break
                    topic = ideas[idea_idx]["topic"]
                    idea_idx += 1
                    schedule_at = post_date.replace(hour=hour, minute=0, second=0, microsecond=0)

                    if platform == Platform.INSTAGRAM:
                        post = self.generate_instagram_post(topic, schedule_at)
                    elif platform == Platform.FACEBOOK:
                        post = self.generate_facebook_post(topic, schedule_at)
                    else:
                        post = self.generate_youtube_post(topic, schedule_at)

                    posts.append(post)

        return posts
