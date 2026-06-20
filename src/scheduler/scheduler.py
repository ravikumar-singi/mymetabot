"""
Auto-posting scheduler.

- Polls the DB for scheduled posts due for publishing.
- Dispatches to the correct platform client.
- Updates post status and logs results.
- Can also run cron-triggered content generation.
"""
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import config
from src.database.db import get_session, init_db
from src.database.models import ContentPost, Platform, PostStatus, PostingLog
from src.logger import get_logger

log = get_logger(__name__)


def _get_platform_client(platform: Platform):
    if platform == Platform.INSTAGRAM:
        from src.platforms.instagram import InstagramClient
        return InstagramClient()
    elif platform == Platform.FACEBOOK:
        from src.platforms.facebook import FacebookClient
        return FacebookClient()
    elif platform == Platform.YOUTUBE:
        from src.platforms.youtube import YouTubeClient
        return YouTubeClient()
    raise ValueError(f"Unknown platform: {platform}")


def publish_due_posts() -> int:
    """Find and publish all posts scheduled for now or earlier. Returns count published."""
    session = get_session()
    published = 0
    try:
        due = (
            session.query(ContentPost)
            .filter(
                ContentPost.status == PostStatus.SCHEDULED,
                ContentPost.scheduled_at <= datetime.utcnow(),
            )
            .all()
        )
        log.info(f"Found {len(due)} post(s) due for publishing.")

        for post in due:
            try:
                client = _get_platform_client(post.platform)
                post_id = client.post(post)
                post.status = PostStatus.POSTED
                post.platform_post_id = post_id
                post.posted_at = datetime.utcnow()
                session.add(PostingLog(post_id=post.id, action="post", message=f"Posted: {post_id}", success=True))
                published += 1
                log.info(f"[{post.platform}] Post {post.id} published → {post_id}")
            except Exception as e:
                post.status = PostStatus.FAILED
                post.error_message = str(e)
                session.add(PostingLog(post_id=post.id, action="post", message=str(e), success=False))
                log.error(f"[{post.platform}] Post {post.id} FAILED: {e}")

        session.commit()
    finally:
        session.close()
    return published


def generate_and_schedule(
    platforms: Optional[list[Platform]] = None,
    weeks: int = 1,
) -> int:
    """Generate new content calendar entries and save them to DB. Returns count created."""
    from src.content.generator import ContentGenerator

    if platforms is None:
        platforms = [Platform.INSTAGRAM, Platform.FACEBOOK, Platform.YOUTUBE]

    gen = ContentGenerator()
    session = get_session()
    count = 0
    try:
        posts = gen.generate_content_calendar(weeks=weeks)
        for post in posts:
            if post.platform in platforms:
                session.add(post)
                count += 1
        session.commit()
        log.info(f"Generated and saved {count} new posts to the calendar.")
    finally:
        session.close()
    return count


class BotScheduler:
    def __init__(self, blocking: bool = True):
        self._sched = BlockingScheduler() if blocking else BackgroundScheduler()

    def start(self):
        init_db()

        # Post publisher — runs every 5 minutes
        self._sched.add_job(publish_due_posts, "interval", minutes=5, id="publish_due")

        # Content generation — weekly on Sunday 00:00 UTC
        self._sched.add_job(
            generate_and_schedule,
            CronTrigger.from_crontab("0 0 * * 0"),
            id="weekly_gen",
        )

        log.info("Scheduler started. Publishing every 5 min. Generating weekly.")
        self._sched.start()

    def stop(self):
        self._sched.shutdown()
