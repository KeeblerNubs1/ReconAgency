import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

def env_bool(name, default=False):
    value=os.getenv(name)
    return default if value is None else value.lower() in {"1","true","yes","on"}

@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    allowed_user_ids: frozenset[int]
    bot_display_name: str
    headless: bool
    log_level: str
    chrome_profile_dir: str

def load_settings():
    token=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
    if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
    ids=frozenset(int(x.strip()) for x in os.getenv("ALLOWED_TELEGRAM_USER_IDS","").split(",") if x.strip())
    if not ids: raise RuntimeError("ALLOWED_TELEGRAM_USER_IDS must contain at least one Telegram user ID")
    return Settings(token, ids, os.getenv("BOT_DISPLAY_NAME","Meeting Bot"), env_bool("HEADLESS",True), os.getenv("LOG_LEVEL","INFO"), os.getenv("CHROME_PROFILE_DIR","/data/chrome-profile"))
