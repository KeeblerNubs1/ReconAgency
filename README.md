# Zoom Telegram Browser Bot

Dockerized Telegram bot using Chromium + Selenium to open the Zoom web client for authorized meetings.

## Features
- `/join <zoom-url>` or send a Zoom URL directly
- `/status`
- `/leave`
- Chromium/Selenium in Docker
- Headless mode
- Camera/microphone/notification permissions denied by default
- Explicit permission/prompt decline handling
- Owner-managed admin list persisted in `/data/admins.json`
- Non-admin access costs 500 Telegram Stars for every submitted Zoom link
- Persistent Chrome profile

## Setup
1. Copy `.env.example` to `.env`.
2. Set `TELEGRAM_BOT_TOKEN` and `OWNER_TELEGRAM_USER_ID`. Fill in `TELEGRAM_API_ID`
   and `TELEGRAM_API_HASH` from [my.telegram.org](https://my.telegram.org) when your
   deployment needs Telegram client API credentials; the bot itself uses its bot token.
3. Run `docker compose up --build -d`.
4. Use `/join https://us06web.zoom.us/j/...` or send that Zoom URL by itself in Telegram.

The owner can manage free-access admins with `/addadmin <Telegram user ID>`,
`/removeadmin <Telegram user ID>`, and `/admins`. Everyone else receives a 500-Star
Telegram invoice each time they submit a valid Zoom URL. A successful payment can be
used once for the specific link that generated its invoice.

Use only where you are authorized to operate the bot. This project does not include stealth/evasion, CAPTCHA bypass, identity spoofing, or access-control bypassing.

Zoom's web UI changes over time, so selectors may require maintenance.
