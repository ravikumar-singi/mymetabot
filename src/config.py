import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent


class Config:
    # Claude AI
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # Meta (Instagram + Facebook)
    META_APP_ID: str = os.getenv("META_APP_ID", "")
    META_APP_SECRET: str = os.getenv("META_APP_SECRET", "")
    INSTAGRAM_ACCOUNT_ID: str = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    FACEBOOK_PAGE_ID: str = os.getenv("FACEBOOK_PAGE_ID", "")
    FACEBOOK_ACCESS_TOKEN: str = os.getenv("FACEBOOK_ACCESS_TOKEN", "")

    # YouTube
    YOUTUBE_CLIENT_SECRETS_FILE: str = os.getenv(
        "YOUTUBE_CLIENT_SECRETS_FILE",
        str(BASE_DIR / "client_secrets.json"),
    )
    YOUTUBE_TOKEN_FILE: str = os.getenv(
        "YOUTUBE_TOKEN_FILE",
        str(BASE_DIR / "youtube_token.json"),
    )
    YOUTUBE_CHANNEL_ID: str = os.getenv("YOUTUBE_CHANNEL_ID", "")

    # Bot personality
    BOT_NICHE: str = os.getenv("BOT_NICHE", "lifestyle")
    BOT_BRAND_NAME: str = os.getenv("BOT_BRAND_NAME", "MyMetaBot")
    BOT_TARGET_AUDIENCE: str = os.getenv("BOT_TARGET_AUDIENCE", "general audience")
    BOT_TONE: str = os.getenv("BOT_TONE", "inspirational")

    # Posting schedules (cron expressions, UTC)
    INSTAGRAM_POST_SCHEDULE: str = os.getenv("INSTAGRAM_POST_SCHEDULE", "0 9 * * 1,3,5")
    FACEBOOK_POST_SCHEDULE: str = os.getenv("FACEBOOK_POST_SCHEDULE", "0 10 * * 1,3,5")
    YOUTUBE_POST_SCHEDULE: str = os.getenv("YOUTUBE_POST_SCHEDULE", "0 14 * * 2,4")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/mymetabot.db")

    # Meta Graph API base
    GRAPH_API_BASE: str = "https://graph.facebook.com/v18.0"

    @classmethod
    def validate(cls) -> list[str]:
        """Return list of missing required config keys."""
        missing = []
        if not cls.ANTHROPIC_API_KEY:
            missing.append("ANTHROPIC_API_KEY")
        return missing


config = Config()
