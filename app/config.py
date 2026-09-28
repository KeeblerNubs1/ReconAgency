import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def env_bool(name, default=False):
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    owner_telegram_user_id: int
    telegram_api_id: str
    telegram_api_hash: str
    bot_display_name: str
    headless: bool
    log_level: str
    chrome_profile_dir: str
    state_dir: str

def load_settings():
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    owner = os.getenv("OWNER_TELEGRAM_USER_ID", "").strip()
    if not owner or not owner.lstrip("-").isdigit():
        raise RuntimeError("OWNER_TELEGRAM_USER_ID must be a Telegram user ID")
    return Settings(
        token,
        int(owner),
        os.getenv("TELEGRAM_API_ID", "").strip(),
        os.getenv("TELEGRAM_API_HASH", "").strip(),
        os.getenv("BOT_DISPLAY_NAME", "Meeting Bot"),
        env_bool("HEADLESS", True),
        os.getenv("LOG_LEVEL", "INFO"),
        os.getenv("CHROME_PROFILE_DIR", "/data/chrome-profile"),
        os.getenv("STATE_DIR", "/data"),
    )
