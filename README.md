# MyMetaBot

An end-to-end AI-powered social media content bot that automatically generates, schedules, and posts content to **Instagram**, **Facebook**, and **YouTube** — powered by Claude AI.

## Features

- **AI Content Generation** — Claude generates platform-optimized captions, hashtags, descriptions, video scripts, and thumbnail prompts
- **Multi-Platform** — Instagram (photos/reels/carousels), Facebook (text/photo/video), YouTube (videos/shorts)
- **Content Calendar** — Auto-generates weeks of content in one command
- **Auto-Scheduler** — Daemon that publishes posts at the right time automatically
- **Topic Ideas Engine** — AI brainstorms fresh topic ideas based on your niche
- **Visual Prompts** — AI generates image prompts you can feed into Stable Diffusion or DALL-E
- **SQLite tracking** — Full audit trail of all posts and logs

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Set up social media credentials

**Instagram & Facebook (Meta):**
1. Create a Meta Developer App at https://developers.facebook.com/apps/
2. Add Instagram Graph API and Facebook Pages products
3. Get your Page Access Token (long-lived, 60 days) and Instagram Business Account ID
4. Run `python scripts/refresh_meta_token.py --token SHORT_LIVED_TOKEN` to exchange for long-lived token

**YouTube:**
1. Create a project at https://console.cloud.google.com/
2. Enable YouTube Data API v3
3. Create OAuth2 credentials (Desktop app), download as `client_secrets.json`
4. Run once: `python scripts/youtube_auth.py` (opens browser for Google login)

### 4. Initialize and run

```bash
# Initialize database
python main.py init

# Generate topic ideas for your niche
python main.py topics

# Generate content for all platforms (saved as drafts)
python main.py generate --topic "10 Morning Habits That Changed My Life"

# Generate a 2-week content calendar
python main.py schedule --weeks 2

# View the calendar
python main.py status --status scheduled

# Post a specific draft immediately
python main.py post 1

# Start the auto-scheduler daemon (runs forever, posts on schedule)
python main.py run
```

## Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize the SQLite database |
| `topics [-n N]` | Generate N topic ideas (default 10) |
| `generate [-p PLATFORM] [-t TOPIC]` | Generate AI content, optionally post immediately with `--post-now` |
| `schedule [-w WEEKS] [-p PLATFORM]` | Generate a full content calendar |
| `post POST_ID` | Immediately publish a post by ID |
| `status [-s STATUS] [-n LIMIT]` | View content calendar / post history |
| `run` | Start the auto-scheduler daemon |

## Project Structure

```
mymetabot/
├── src/
│   ├── config.py              # All configuration via .env
│   ├── logger.py              # Logging (console + file)
│   ├── content/
│   │   ├── generator.py       # Claude AI content generation
│   │   └── templates.py       # Platform prompts & specs
│   ├── platforms/
│   │   ├── instagram.py       # Instagram Graph API
│   │   ├── facebook.py        # Facebook Pages API
│   │   └── youtube.py         # YouTube Data API v3
│   ├── scheduler/
│   │   └── scheduler.py       # APScheduler-based auto-poster
│   └── database/
│       ├── models.py           # SQLAlchemy models
│       └── db.py               # DB session management
├── scripts/
│   ├── youtube_auth.py         # One-time YouTube OAuth setup
│   └── refresh_meta_token.py   # Refresh Instagram/Facebook token
├── tests/
├── main.py                     # CLI entry point
├── .env.example                # Config template
└── requirements.txt
```

## Content Pipeline

```
Topic Ideas (Claude)
       ↓
Platform Content (Claude)
  Instagram: caption + hashtags + image_prompt
  Facebook:  title + caption + hashtags + image_prompt
  YouTube:   title + description + tags + script + thumbnail_prompt
       ↓
Saved to SQLite (status: scheduled)
       ↓
Generate image/video (Stable Diffusion / DALL-E / your own)
Set media_url on the post
       ↓
Scheduler posts at optimal time (status: posted)
```

## Environment Variables

See `.env.example` for full documentation of all variables.

Key variables:
- `ANTHROPIC_API_KEY` — Required for content generation
- `BOT_NICHE` — Your account niche (e.g. `fitness`, `travel`, `tech`)
- `BOT_BRAND_NAME` — Your brand name
- `BOT_TONE` — Voice tone: `professional` / `casual` / `humorous` / `inspirational`

## Running Tests

```bash
pytest tests/ -v
```