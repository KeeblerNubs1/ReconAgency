import logging
from telegram import Update
from telegram.ext import Application,CommandHandler,ContextTypes
from .zoom_browser import ZoomBrowser
log=logging.getLogger(__name__)
class TelegramZoomBot:
    def __init__(self,token,allowed_user_ids,zoom):
        self.allowed_user_ids=allowed_user_ids;self.zoom=zoom
        self.application=Application.builder().token(token).build()
        for name,fn in [("start",self.start),("help",self.help),("join",self.join),("status",self.status),("leave",self.leave)]:self.application.add_handler(CommandHandler(name,fn))
    def auth(self,u):return bool(u.effective_user and u.effective_user.id in self.allowed_user_ids)
    async def deny(self,u):
        if u.message:await u.message.reply_text("Not authorized.")
    async def start(self,u,c):
        if not self.auth(u):return await self.deny(u)
        await u.message.reply_text("Ready. Use /join <Zoom URL>, /status, /leave")
    async def help(self,u,c):
        if not self.auth(u):return await self.deny(u)
        await u.message.reply_text("/join <zoom-url> - start an authorized browser session\n/status - show status\n/leave - stop it")
    async def join(self,u,c):
        if not self.auth(u):return await self.deny(u)
        if not c.args:return await u.message.reply_text("Usage: /join https://us06web.zoom.us/j/MEETING_ID")
        url=c.args[0].strip()
        if not ZoomBrowser.validate_zoom_url(url):return await u.message.reply_text("That is not a valid zoom.us URL.")
        try:self.zoom.start(url)
        except (RuntimeError,ValueError) as e:return await u.message.reply_text(str(e))
        await u.message.reply_text("Browser session starting. Camera and microphone are configured off.")
    async def status(self,u,c):
        if not self.auth(u):return await self.deny(u)
        s=self.zoom.snapshot()
        if not s:return await u.message.reply_text("No meeting session.")
        await u.message.reply_text(f"Status: {s.status}\nMessage: {s.message}\nURL: {s.url}")
    async def leave(self,u,c):
        if not self.auth(u):return await self.deny(u)
        self.zoom.stop();await u.message.reply_text("Browser session stopped.")
    def run(self):self.application.run_polling(drop_pending_updates=True)
