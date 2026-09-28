# Zoom Telegram Browser Bot

Dockerized Telegram bot using Chromium + Selenium to open the Zoom web client for authorized meetings.

## Features
- `/join <zoom-url>`
- `/status`
- `/leave`
- Chromium/Selenium in Docker
- Headless mode
- Camera/microphone/notification permissions denied by default
- Explicit permission/prompt decline handling
- Authorized Telegram user allowlist
- Persistent Chrome profile

## Setup
1. Copy `.env.example` to `.env`.
2. Set `TELEGRAM_BOT_TOKEN` and `ALLOWED_TELEGRAM_USER_IDS`.
3. Run `docker compose up --build -d`.
4. Use `/join https://us06web.zoom.us/j/...` in Telegram.

Use only where you are authorized to operate the bot. This project does not include stealth/evasion, CAPTCHA bypass, identity spoofing, or access-control bypassing.

Zoom's web UI changes over time, so selectors may require maintenance.
