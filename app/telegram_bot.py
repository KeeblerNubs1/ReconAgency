import asyncio
import logging
from telegram import Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import Application,CommandHandler,ContextTypes,MessageHandler,filters
from .zoom_browser import ZoomBrowser
log=logging.getLogger(__name__)


class TelegramZoomBot:
    def __init__(self,token,allowed_user_ids,zoom):
        self.allowed_user_ids=allowed_user_ids;self.zoom=zoom
        self.application=Application.builder().token(token).build()
        for name,fn in [("start",self.start),("help",self.help),("join",self.join),("status",self.status),("leave",self.leave)]:self.application.add_handler(CommandHandler(name,fn))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,self.join_from_message))
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
        await self.start_meeting(u,c.args[0])
    async def join_from_message(self,u,c):
        if not self.auth(u):return await self.deny(u)
        url=(u.message.text or "").strip()
        if not ZoomBrowser.validate_zoom_url(url):return
        await self.start_meeting(u,url)
    async def start_meeting(self,u,url):
        url=url.strip()
        if not ZoomBrowser.validate_zoom_url(url):return await u.message.reply_text("That is not a valid zoom.us URL.")
        try:self.zoom.start(url)
        except (RuntimeError,ValueError) as e:return await u.message.reply_text(str(e))
        message=await u.message.reply_text(self.format_status())
        self.application.create_task(self.update_live_status(message),name="zoom-live-status")

    def format_status(self):
        state=self.zoom.snapshot()
        if not state:return "No meeting session."
        return f"Status: {state.status}\nMessage: {state.message}\nURL: {state.url}"

    async def update_live_status(self,message):
        """Edit the initial join reply as the browser session progresses."""
        previous=message.text
        while True:
            await asyncio.sleep(1)
            text=self.format_status()
            if text != previous:
                try:
                    await message.edit_text(text)
                except BadRequest as error:
                    if "Message is not modified" not in str(error):
                        log.warning("Unable to update live Zoom status: %s",error)
                        return
                except TelegramError:
                    log.exception("Unable to update live Zoom status")
                    return
                previous=text
            state=self.zoom.snapshot()
            if not state or state.status in {"error","stopped"}:
                return

    async def status(self,u,c):
        if not self.auth(u):return await self.deny(u)
        await u.message.reply_text(self.format_status())
    async def leave(self,u,c):
        if not self.auth(u):return await self.deny(u)
        self.zoom.stop();await u.message.reply_text("Browser session stopped.")
    def run(self):self.application.run_polling(drop_pending_updates=True)
