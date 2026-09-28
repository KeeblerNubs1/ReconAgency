import logging

from telegram import LabeledPrice, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from .zoom_browser import ZoomBrowser

log = logging.getLogger(__name__)
STAR_PRICE = 500
PAYMENT_PREFIX = "zoom-join:"


class TelegramZoomBot:
    def __init__(self, token, owner_id, admins, payments, zoom):
        self.owner_id = owner_id
        self.admins = admins
        self.payments = payments
        self.zoom = zoom
        self.application = Application.builder().token(token).build()
        for name, handler in [
            ("start", self.start), ("help", self.help), ("join", self.join),
            ("status", self.status), ("leave", self.leave),
            ("addadmin", self.add_admin), ("removeadmin", self.remove_admin),
            ("admins", self.list_admins),
        ]:
            self.application.add_handler(CommandHandler(name, handler))
        self.application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, self.successful_payment))
        self.application.add_handler(PreCheckoutQueryHandler(self.pre_checkout))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.join_from_message))

    @staticmethod
    def user_id(update):
        return update.effective_user.id if update.effective_user else None

    def is_admin(self, update):
        user_id = self.user_id(update)
        return user_id is not None and self.admins.is_admin(user_id)

    def is_owner(self, update):
        return self.user_id(update) == self.owner_id

    async def owner_only(self, update):
        if update.message:
            await update.message.reply_text("Only the owner can manage admins.")

    async def start(self, update, context):
        await update.message.reply_text(
            "Send a Zoom URL or use /join <Zoom URL>. Admins join for free; everyone else pays 500 Telegram Stars per link."
        )

    async def help(self, update, context):
        await update.message.reply_text(
            "/join <zoom-url> - join a meeting\n/status - show status\n/leave - stop it\n"
            "Owner: /addadmin <user-id>, /removeadmin <user-id>, /admins"
        )

    async def add_admin(self, update, context):
        if not self.is_owner(update):
            return await self.owner_only(update)
        user_id = self.command_user_id(context)
        if user_id is None:
            return await update.message.reply_text("Usage: /addadmin <Telegram user ID>")
        self.admins.add(user_id)
        await update.message.reply_text(f"Added {user_id} as an admin.")

    async def remove_admin(self, update, context):
        if not self.is_owner(update):
            return await self.owner_only(update)
        user_id = self.command_user_id(context)
        if user_id is None:
            return await update.message.reply_text("Usage: /removeadmin <Telegram user ID>")
        if user_id == self.owner_id:
            return await update.message.reply_text("The owner cannot be removed.")
        self.admins.remove(user_id)
        await update.message.reply_text(f"Removed {user_id} from the admin list.")

    async def list_admins(self, update, context):
        if not self.is_owner(update):
            return await self.owner_only(update)
        user_ids = sorted(self.admins.admin_ids() | {self.owner_id})
        await update.message.reply_text("Admins:\n" + "\n".join(map(str, user_ids)))

    @staticmethod
    def command_user_id(context):
        if len(context.args) != 1 or not context.args[0].lstrip("-").isdigit():
            return None
        return int(context.args[0])

    async def join(self, update, context):
        if not context.args:
            return await update.message.reply_text("Usage: /join https://us06web.zoom.us/j/MEETING_ID")
        await self.request_join(update, context.args[0])

    async def join_from_message(self, update, context):
        url = (update.message.text or "").strip()
        if ZoomBrowser.validate_zoom_url(url):
            await self.request_join(update, url)

    async def request_join(self, update, url):
        url = url.strip()
        if not ZoomBrowser.validate_zoom_url(url):
            return await update.message.reply_text("That is not a valid zoom.us URL.")
        if self.is_admin(update):
            return await self.start_meeting(update, url)
        payment_id = self.payments.create(self.user_id(update), url)
        await update.message.reply_invoice(
            title="Zoom link access",
            description="One Zoom link submission",
            payload=PAYMENT_PREFIX + payment_id,
            currency="XTR",
            prices=[LabeledPrice("Zoom link access", STAR_PRICE)],
            provider_token="",
        )

    async def pre_checkout(self, update, context):
        query = update.pre_checkout_query
        valid = (
            query.currency == "XTR" and query.total_amount == STAR_PRICE
            and query.invoice_payload.startswith(PAYMENT_PREFIX)
        )
        await query.answer(ok=valid, error_message=None if valid else "This payment is invalid. Please send the link again.")

    async def successful_payment(self, update, context):
        payment = update.message.successful_payment
        if payment.currency != "XTR" or payment.total_amount != STAR_PRICE:
            log.warning("Rejected unexpected payment amount from user %s", self.user_id(update))
            return
        payload = payment.invoice_payload
        if not payload.startswith(PAYMENT_PREFIX):
            return
        url = self.payments.redeem(payload.removeprefix(PAYMENT_PREFIX), self.user_id(update))
        if not url:
            return await update.message.reply_text("This payment was already used or has expired. Contact the owner if you were charged.")
        await self.start_meeting(update, url)

    async def start_meeting(self, update, url):
        try:
            self.zoom.start(url)
        except (RuntimeError, ValueError) as error:
            return await update.message.reply_text(str(error))
        await update.message.reply_text("Browser session starting. Camera and microphone are configured off.")

    async def status(self, update, context):
        if not self.is_admin(update):
            return await update.message.reply_text("Only admins can view meeting status.")
        snapshot = self.zoom.snapshot()
        if not snapshot:
            return await update.message.reply_text("No meeting session.")
        await update.message.reply_text(f"Status: {snapshot.status}\nMessage: {snapshot.message}\nURL: {snapshot.url}")

    async def leave(self, update, context):
        if not self.is_admin(update):
            return await update.message.reply_text("Only admins can stop the browser session.")
        self.zoom.stop()
        await update.message.reply_text("Browser session stopped.")

    def run(self):
        self.application.run_polling(drop_pending_updates=True)
