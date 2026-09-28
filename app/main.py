from pathlib import Path

from .access import AdminStore, PaymentStore
from .config import load_settings
from .logger import configure_logging
from .telegram_bot import TelegramZoomBot
from .zoom_browser import ZoomBrowser


def main():
    s = load_settings()
    configure_logging(s.log_level)
    z = ZoomBrowser(s.chrome_profile_dir, s.bot_display_name, s.headless)
    state_dir = Path(s.state_dir)
    admins = AdminStore(state_dir / "admins.json", s.owner_telegram_user_id)
    payments = PaymentStore(state_dir / "payments.json")
    TelegramZoomBot(s.telegram_bot_token, s.owner_telegram_user_id, admins, payments, z).run()


if __name__ == '__main__':
    main()
