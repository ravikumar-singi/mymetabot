from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    JSON,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Platform(str, PyEnum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    YOUTUBE = "youtube"


class PostStatus(str, PyEnum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"
    SKIPPED = "skipped"


class ContentPost(Base):
    __tablename__ = "content_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(Enum(Platform), nullable=False)
    status = Column(Enum(PostStatus), default=PostStatus.DRAFT, nullable=False)

    topic = Column(String(255))
    niche = Column(String(100))

    # Platform-specific content fields
    title = Column(String(500))           # YouTube title / Facebook heading
    caption = Column(Text)                # Instagram/Facebook caption
    hashtags = Column(Text)               # Space-separated hashtags
    description = Column(Text)            # YouTube description
    tags = Column(Text)                   # YouTube comma-separated tags
    script = Column(Text)                 # YouTube Shorts/video script
    image_prompt = Column(Text)           # Prompt for AI image generation
    media_url = Column(String(1000))      # URL of media to post

    # Metadata
    platform_post_id = Column(String(255))  # ID returned by the platform API
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)
    error_message = Column(Text)
    extra = Column(JSON)                   # Any extra platform-specific data

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        plat = self.platform.value if self.platform else None
        stat = self.status.value if self.status else None
        return f"<ContentPost id={self.id} platform={plat} status={stat}>"


class PostingLog(Base):
    __tablename__ = "posting_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("content_posts.id"), nullable=False)
    action = Column(String(100))
    message = Column(Text)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("ContentPost", backref="logs")
