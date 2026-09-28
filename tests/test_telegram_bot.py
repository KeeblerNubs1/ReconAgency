import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.telegram_bot import TelegramZoomBot


class LiveStatusMessage:
    def __init__(self, text):
        self.text = text
        self.edit_text = AsyncMock()


class LiveStatusTests(unittest.IsolatedAsyncioTestCase):
    @patch("app.telegram_bot.asyncio.sleep", new_callable=AsyncMock)
    async def test_edits_join_reply_when_browser_status_changes(self, sleep):
        bot = TelegramZoomBot.__new__(TelegramZoomBot)
        states = iter(
            [
                SimpleNamespace(status="joining", message="Zoom page loaded", url="https://zoom.us/j/1"),
                SimpleNamespace(status="stopped", message="Session stopped", url="https://zoom.us/j/1"),
            ]
        )
        bot.zoom = SimpleNamespace(snapshot=lambda: next(states))
        message = LiveStatusMessage("Status: starting\nMessage: Launching Chromium\nURL: https://zoom.us/j/1")

        await bot.update_live_status(message)

        message.edit_text.assert_awaited_once_with(
            "Status: joining\nMessage: Zoom page loaded\nURL: https://zoom.us/j/1"
        )
        sleep.assert_awaited_once_with(1)


class FormatStatusTests(unittest.TestCase):
    def test_formats_a_snapshot_for_status_and_live_updates(self):
        bot = TelegramZoomBot.__new__(TelegramZoomBot)
        bot.zoom = SimpleNamespace(
            snapshot=lambda: SimpleNamespace(
                status="joining", message="Zoom page loaded", url="https://zoom.us/j/1"
            )
        )

        self.assertEqual(
            bot.format_status(),
            "Status: joining\nMessage: Zoom page loaded\nURL: https://zoom.us/j/1",
        )
