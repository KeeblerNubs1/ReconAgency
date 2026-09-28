import unittest
from unittest.mock import patch

from app.zoom_browser import ZoomBrowser


class Element:
    def __init__(self,label):
        self.label=label
        self.clicked=False

    def get_attribute(self,name):
        assert name == "aria-label"
        return self.label

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def click(self):
        self.clicked=True


class Driver:
    def __init__(self,elements):
        self.elements=elements

    def find_elements(self,by,selector):
        if "stop video" in selector:
            return [element for element in self.elements if "video" in element.label.lower()]
        return [element for element in self.elements if "mute" in element.label.lower()]


class DisableMediaTests(unittest.TestCase):
    @patch("app.zoom_browser.time.sleep")
    def test_disables_active_media_without_unmuting(self,sleep):
        stop_video=Element("Stop Video")
        mute=Element("Mute microphone")
        unmute=Element("Unmute microphone")
        driver=Driver([stop_video,mute,unmute])

        ZoomBrowser("/tmp/profile","Meeting Bot").disable_media_if_visible(driver)

        self.assertTrue(stop_video.clicked)
        self.assertTrue(mute.clicked)
        self.assertFalse(unmute.clicked)

