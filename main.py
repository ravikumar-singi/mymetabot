#!/usr/bin/env python3
"""
MyMetaBot — Auto social media content generator & poster.

Commands:
  init          Initialize the database
  generate      Generate content for one or all platforms
  schedule      Generate a full content calendar (multi-week)
  post          Immediately post a draft/scheduled post by ID
  run           Start the auto-scheduler daemon
  status        Show upcoming and recent posts
  topics        Generate and display topic ideas
"""
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table

from src.config import config
from src.database.db import init_db, get_session
from src.database.models import ContentPost, Platform, PostStatus
from src.logger import get_logger

log = get_logger("cli")
console = Console()


def _ensure_api_key():
    missing = config.validate()
    if missing:
        console.print(f"[red]Missing required config: {', '.join(missing)}[/red]")
        console.print("Copy .env.example to .env and fill in your API keys.")
        sys.exit(1)


@click.group()
def cli():
    """MyMetaBot — End-to-end AI social media content generator."""


@cli.command()
def init():
    """Initialize the database."""
    init_db()
    console.print("[green]Database initialized.[/green]")


@cli.command()
@click.option("--platform", "-p", type=click.Choice(["instagram", "facebook", "youtube", "all"]), default="all")
@click.option("--topic", "-t", help="Custom topic (auto-generated if omitted)")
@click.option("--post-now", is_flag=True, help="Immediately post instead of saving as draft")
def generate(platform: str, topic: str, post_now: bool):
    """Generate AI content for one or all platforms."""
    _ensure_api_key()
    init_db()
    from src.content.generator import ContentGenerator
    gen = ContentGenerator()

    if not topic:
        ideas = gen.generate_topic_ideas(count=3)
        topic = ideas[0]["topic"]
        console.print(f"[cyan]Auto-selected topic:[/cyan] {topic}")

    platforms_to_generate = (
        [Platform.INSTAGRAM, Platform.FACEBOOK, Platform.YOUTUBE]
        if platform == "all"
        else [Platform(platform)]
    )

    session = get_session()
    try:
        for plat in platforms_to_generate:
            console.print(f"\n[bold]Generating for {plat.value}...[/bold]")
            if plat == Platform.INSTAGRAM:
                post = gen.generate_instagram_post(topic)
            elif plat == Platform.FACEBOOK:
                post = gen.generate_facebook_post(topic)
            else:
                post = gen.generate_youtube_post(topic)

            if post_now:
                from src.scheduler.scheduler import _get_platform_client
                try:
                    client = _get_platform_client(plat)
                    pid = client.post(post)
                    post.status = PostStatus.POSTED
                    post.platform_post_id = pid
                    post.posted_at = datetime.utcnow()
                    console.print(f"[green]Posted to {plat.value}: {pid}[/green]")
                except Exception as e:
                    post.status = PostStatus.FAILED
                    post.error_message = str(e)
                    console.print(f"[red]Failed to post to {plat.value}: {e}[/red]")
            else:
                post.status = PostStatus.DRAFT

            session.add(post)
            session.commit()
            session.refresh(post)
            _print_post(post)
    finally:
        session.close()


@cli.command()
@click.option("--weeks", "-w", default=2, show_default=True, help="Number of weeks to schedule")
@click.option(
    "--platform", "-p",
    multiple=True,
    type=click.Choice(["instagram", "facebook", "youtube"]),
    help="Platforms to generate for (default: all)",
)
def schedule(weeks: int, platform: tuple):
    """Generate a full AI content calendar and save it to the database."""
    _ensure_api_key()
    init_db()
    from src.scheduler.scheduler import generate_and_schedule
    platforms = [Platform(p) for p in platform] if platform else None
    count = generate_and_schedule(platforms=platforms, weeks=weeks)
    console.print(f"[green]Scheduled {count} posts across {weeks} week(s).[/green]")


@cli.command()
@click.argument("post_id", type=int)
def post(post_id: int):
    """Immediately publish a specific post by ID."""
    _ensure_api_key()
    init_db()
    session = get_session()
    try:
        content = session.get(ContentPost, post_id)
        if not content:
            console.print(f"[red]Post {post_id} not found.[/red]")
            return
        from src.scheduler.scheduler import _get_platform_client
        client = _get_platform_client(content.platform)
        pid = client.post(content)
        content.status = PostStatus.POSTED
        content.platform_post_id = pid
        content.posted_at = datetime.utcnow()
        session.commit()
        console.print(f"[green]Posted! Platform ID: {pid}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if session:
            content.status = PostStatus.FAILED
            content.error_message = str(e)
            session.commit()
    finally:
        session.close()


@cli.command()
def run():
    """Start the auto-scheduler daemon (blocking)."""
    _ensure_api_key()
    from src.scheduler.scheduler import BotScheduler
    console.print("[bold green]Starting MyMetaBot scheduler...[/bold green]")
    console.print("Press Ctrl+C to stop.")
    try:
        BotScheduler(blocking=True).start()
    except (KeyboardInterrupt, SystemExit):
        console.print("\n[yellow]Scheduler stopped.[/yellow]")


@cli.command()
@click.option("--limit", "-n", default=20, show_default=True)
@click.option(
    "--status", "-s",
    type=click.Choice(["draft", "scheduled", "posted", "failed", "all"]),
    default="all",
)
def status(limit: int, status: str):
    """Show upcoming and recent posts."""
    init_db()
    session = get_session()
    try:
        q = session.query(ContentPost)
        if status != "all":
            q = q.filter(ContentPost.status == PostStatus(status))
        posts = q.order_by(ContentPost.scheduled_at.nullslast(), ContentPost.created_at.desc()).limit(limit).all()
        _print_posts_table(posts)
    finally:
        session.close()


@cli.command()
@click.option("--count", "-n", default=10, show_default=True)
def topics(count: int):
    """Generate and display AI topic ideas."""
    _ensure_api_key()
    from src.content.generator import ContentGenerator
    gen = ContentGenerator()
    ideas = gen.generate_topic_ideas(count=count)

    table = Table(title=f"Topic Ideas — {config.BOT_NICHE.title()} / {config.BOT_BRAND_NAME}")
    table.add_column("#", style="dim", width=3)
    table.add_column("Topic", style="bold")
    table.add_column("Pillar")
    table.add_column("Hook")
    table.add_column("Platforms")

    for i, idea in enumerate(ideas, 1):
        table.add_row(
            str(i),
            idea.get("topic", ""),
            idea.get("pillar", ""),
            idea.get("hook", ""),
            ", ".join(idea.get("platforms", [])),
        )
    console.print(table)


def _print_post(post: ContentPost):
    console.print(f"\n[bold cyan]─── {post.platform.value.upper()} Post (ID: {post.id}) ───[/bold cyan]")
    if post.title:
        console.print(f"[bold]Title:[/bold] {post.title}")
    if post.caption:
        preview = post.caption[:200] + ("..." if len(post.caption) > 200 else "")
        console.print(f"[bold]Caption:[/bold] {preview}")
    if post.hashtags:
        console.print(f"[bold]Hashtags:[/bold] {post.hashtags[:120]}...")
    if post.script:
        console.print(f"[bold]Script:[/bold] {post.script[:150]}...")
    if post.image_prompt:
        console.print(f"[bold]Visual:[/bold] {post.image_prompt[:120]}...")
    console.print(f"[bold]Status:[/bold] {post.status.value}")


def _print_posts_table(posts: list[ContentPost]):
    table = Table(title="MyMetaBot Content Calendar")
    table.add_column("ID", width=5)
    table.add_column("Platform")
    table.add_column("Topic")
    table.add_column("Status")
    table.add_column("Scheduled At")
    table.add_column("Posted At")

    status_styles = {
        PostStatus.DRAFT: "dim",
        PostStatus.SCHEDULED: "cyan",
        PostStatus.POSTED: "green",
        PostStatus.FAILED: "red",
        PostStatus.SKIPPED: "yellow",
    }

    for p in posts:
        style = status_styles.get(p.status, "")
        table.add_row(
            str(p.id),
            p.platform.value,
            (p.topic or "")[:40],
            f"[{style}]{p.status.value}[/{style}]",
            str(p.scheduled_at)[:16] if p.scheduled_at else "—",
            str(p.posted_at)[:16] if p.posted_at else "—",
        )
    console.print(table)


if __name__ == "__main__":
    cli()
