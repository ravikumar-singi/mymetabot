from dataclasses import dataclass
from src.database.models import Platform


@dataclass
class PlatformSpec:
    caption_limit: int
    hashtag_count: int
    optimal_post_length: str
    content_types: list[str]
    image_ratio: str


PLATFORM_SPECS: dict[Platform, PlatformSpec] = {
    Platform.INSTAGRAM: PlatformSpec(
        caption_limit=2200,
        hashtag_count=30,
        optimal_post_length="100-150 words",
        content_types=["photo", "carousel", "reel", "story"],
        image_ratio="1:1 or 4:5",
    ),
    Platform.FACEBOOK: PlatformSpec(
        caption_limit=63206,
        hashtag_count=10,
        optimal_post_length="40-80 words",
        content_types=["text", "photo", "video", "link", "story"],
        image_ratio="16:9 or 1:1",
    ),
    Platform.YOUTUBE: PlatformSpec(
        caption_limit=5000,
        hashtag_count=15,
        optimal_post_length="150-300 words for description",
        content_types=["video", "shorts", "live"],
        image_ratio="16:9",
    ),
}


SYSTEM_PROMPT_TEMPLATE = """\
You are a professional social media content creator and copywriter for the brand "{brand_name}".
Niche: {niche}
Target audience: {target_audience}
Tone of voice: {tone}

You specialize in creating engaging, authentic, and viral-worthy social media content.
Always write in the brand's voice and ensure content resonates with the target audience.
Never use generic filler phrases. Be specific, engaging, and action-oriented.
"""

INSTAGRAM_PROMPT = """\
Create an Instagram post about the topic: "{topic}"

Requirements:
- Caption: engaging, {length}, ends with a call-to-action
- Include {hashtags} relevant hashtags (mix of popular and niche-specific)
- Suggest an image/visual description that would perform well
- Use emojis naturally throughout

Return a JSON object with these exact keys:
{{
  "caption": "the full caption text with emojis",
  "hashtags": "space-separated hashtags starting with #",
  "image_prompt": "detailed description for AI image generation (style, subject, mood, colors)",
  "image_alt": "accessibility alt text for the image"
}}
"""

FACEBOOK_PROMPT = """\
Create a Facebook post about the topic: "{topic}"

Requirements:
- Post text: conversational, {length}, encourages comments/shares
- Include {hashtags} relevant hashtags
- Suggest an engaging image or visual
- Add a hook in the first sentence to stop the scroll

Return a JSON object with these exact keys:
{{
  "title": "attention-grabbing first sentence (the hook)",
  "caption": "full post body text",
  "hashtags": "space-separated hashtags starting with #",
  "image_prompt": "detailed description for AI image generation (style, subject, mood, colors)",
  "call_to_action": "specific question or CTA to boost engagement"
}}
"""

YOUTUBE_PROMPT = """\
Create a YouTube video plan about the topic: "{topic}"

Requirements:
- Title: SEO-optimized, curiosity-driven, under 60 characters
- Description: SEO-rich, includes timestamps placeholder, links section, and CTA, {length}
- Tags: {hashtags} relevant tags
- Shorts Script: 60-second punchy script for a YouTube Shorts version
- Thumbnail concept: what should appear on the thumbnail

Return a JSON object with these exact keys:
{{
  "title": "YouTube video title",
  "description": "full YouTube video description (with timestamps placeholder)",
  "tags": "comma-separated tags without #",
  "hashtags": "#tag1 #tag2 ... (top 3-5 for description)",
  "script": "full 60-second YouTube Shorts script with [HOOK], [CONTENT], [CTA] sections",
  "thumbnail_prompt": "detailed image description for thumbnail generation",
  "thumbnail_text": "bold text overlay for thumbnail (max 5 words)"
}}
"""

TOPIC_IDEAS_PROMPT = """\
Generate {count} fresh, trending content topic ideas for a {niche} brand targeting {audience}.

Mix these content pillars:
1. Educational / How-to
2. Inspirational / Motivational
3. Behind-the-scenes / Personal
4. Trending / Viral
5. Product/Service showcase
6. User engagement / Questions

Return a JSON array of objects:
[
  {{
    "topic": "specific topic title",
    "pillar": "content pillar category",
    "hook": "one-sentence attention-grabbing angle",
    "platforms": ["instagram", "facebook", "youtube"]
  }},
  ...
]
"""
