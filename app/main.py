from .config import load_settings
from .logger import configure_logging
from .telegram_bot import TelegramZoomBot
from .zoom_browser import ZoomBrowser
def main():
    s=load_settings();configure_logging(s.log_level)
    z=ZoomBrowser(s.chrome_profile_dir,s.bot_display_name,s.headless)
    TelegramZoomBot(s.telegram_bot_token,s.allowed_user_ids,z).run()
if __name__=='__main__':main()
