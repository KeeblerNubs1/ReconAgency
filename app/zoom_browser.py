import logging,re,threading,time
from dataclasses import dataclass
from urllib.parse import urlparse
from selenium import webdriver
from selenium.common.exceptions import WebDriverException,StaleElementReferenceException,ElementClickInterceptedException
from selenium.webdriver.common.by import By
log=logging.getLogger(__name__)
ZOOM_HOST_RE=re.compile(r"^(?:[^./]+\.)?zoom\.us$",re.I)
@dataclass
class MeetingState:
    url:str; status:str="starting"; message:str=""
class ZoomBrowser:
    def __init__(self,profile_dir,display_name,headless=True):
        self.profile_dir=profile_dir; self.display_name=display_name; self.headless=headless; self.driver=None; self.thread=None; self.stop_event=threading.Event(); self.state=None; self.lock=threading.RLock()
    @staticmethod
    def validate_zoom_url(url):
        try:
            p=urlparse(url.strip()); return p.scheme in {"http","https"} and bool(p.hostname) and bool(ZOOM_HOST_RE.match(p.hostname))
        except ValueError:return False
    def start(self,url):
        if not self.validate_zoom_url(url): raise ValueError("Only a valid zoom.us HTTP/HTTPS URL is accepted.")
        with self.lock:
            if self.thread and self.thread.is_alive(): raise RuntimeError("A meeting session is already running.")
            self.stop_event.clear(); self.state=MeetingState(url); self.thread=threading.Thread(target=self._run,daemon=True); self.thread.start()
    def stop(self):
        self.stop_event.set()
        with self.lock: d=self.driver
        if d:
            try:d.quit()
            except WebDriverException:pass
    def snapshot(self):
        with self.lock:
            return None if not self.state else MeetingState(self.state.url,self.state.status,self.state.message)
    def _set(self,status,message=""):
        with self.lock:
            if self.state:self.state.status=status; self.state.message=message
    def _build(self):
        o=webdriver.ChromeOptions()
        if self.headless:o.add_argument("--headless=new")
        o.add_argument("--no-sandbox");o.add_argument("--disable-dev-shm-usage");o.add_argument("--disable-gpu");o.add_argument("--window-size=1920,1080");o.add_argument(f"--user-data-dir={self.profile_dir}")
        o.add_experimental_option("prefs",{"profile.default_content_setting_values.media_stream_mic":2,"profile.default_content_setting_values.media_stream_camera":2,"profile.default_content_setting_values.notifications":2})
        d=webdriver.Chrome(options=o);d.set_page_load_timeout(45);return d
    def _run(self):
        d=None
        try:
            self._set("starting","Launching Chromium");d=self._build()
            with self.lock:self.driver=d
            d.get(self.state.url);self._set("joining","Zoom page loaded")
            deadline=time.time()+45
            while time.time()<deadline and not self.stop_event.is_set():
                self.handle_permission_prompts(d);self.disable_media_if_visible(d);self.try_enter_name(d);self.try_click_join(d);time.sleep(1)
            if self.stop_event.is_set():return
            self._set("monitoring","Browser session is running")
            while not self.stop_event.is_set():
                self.handle_permission_prompts(d);self.disable_media_if_visible(d)
                try:self._set("monitoring",f"Page: {d.title}")
                except WebDriverException:pass
                time.sleep(2)
        except Exception as e:
            log.exception("Zoom browser session failed");self._set("error",str(e))
        finally:
            if d:
                try:d.quit()
                except WebDriverException:pass
            with self.lock:self.driver=None
            if self.stop_event.is_set():self._set("stopped","Session stopped")
    def handle_permission_prompts(self,d):
        selectors=[(By.CSS_SELECTOR,"button[aria-label*='Decline' i]"),(By.CSS_SELECTOR,"button[title*='Decline' i]"),(By.XPATH,"//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'decline')]"),(By.XPATH,"//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),\"don't allow\")]")]
        for by,s in selectors:
            try:
                for e in d.find_elements(by,s):
                    if e.is_displayed() and e.is_enabled():e.click();time.sleep(.3)
            except (StaleElementReferenceException,ElementClickInterceptedException,WebDriverException):continue
    def disable_media_if_visible(self,d):
        controls=[
            ("//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'stop video')]",lambda label:"stop video" in label),
            ("//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'mute')]",lambda label:"mute" in label and "unmute" not in label),
        ]
        for s,should_click in controls:
            try:
                for e in d.find_elements(By.XPATH,s):
                    label=(e.get_attribute("aria-label") or "").lower()
                    if e.is_displayed() and e.is_enabled() and should_click(label):e.click();time.sleep(.3)
            except (StaleElementReferenceException,WebDriverException):continue
    def try_enter_name(self,d):
        for by,s in [(By.ID,"input-for-name"),(By.CSS_SELECTOR,"input[placeholder*='name' i]"),(By.CSS_SELECTOR,"input[aria-label*='name' i]")]:
            try:
                for e in d.find_elements(by,s):
                    if e.is_displayed() and e.is_enabled():e.clear();e.send_keys(self.display_name);return
            except (StaleElementReferenceException,WebDriverException):continue
    def try_click_join(self,d):
        for by,s in [(By.XPATH,"//button[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'join')]"),(By.XPATH,"//a[contains(translate(.,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'join')]")]:
            try:
                for e in d.find_elements(by,s):
                    if e.is_displayed() and e.is_enabled() and 'join' in (e.text or '').lower():e.click();return
            except (StaleElementReferenceException,ElementClickInterceptedException,WebDriverException):continue
