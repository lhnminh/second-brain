"""A fresh browser owned by one handoff, never the user's existing browser."""

import ipaddress
import re
import socket
import sys
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

WIDTH, HEIGHT = 1280, 800


class BrowserActionError(ValueError):
    """A safe, user-readable guard failure, containing no submitted values."""


def public_url(value, *, resolve=True):
    if not isinstance(value, str) or len(value) > 2000:
        raise BrowserActionError("Use a public http:// or https:// website URL")
    url = urlsplit(value)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username
        or url.password
    ):
        raise BrowserActionError("Use a public http:// or https:// website URL")
    host = url.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise BrowserActionError("Local and private-network addresses are unavailable")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise BrowserActionError("Local and private-network addresses are unavailable")
    if url.port not in {None, 80, 443}:
        raise BrowserActionError("Only standard website ports are supported")
    if resolve:
        try:
            addresses = socket.getaddrinfo(
                host,
                url.port or (443 if url.scheme == "https" else 80),
                type=socket.SOCK_STREAM,
            )
        except OSError:
            raise BrowserActionError(
                "The website address could not be resolved"
            ) from None
        if not addresses or any(
            not ipaddress.ip_address(a[4][0]).is_global for a in addresses
        ):
            raise BrowserActionError(
                "Local and private-network addresses are unavailable"
            )
    return value


def safe_filename(value):
    return (
        re.sub(r"[^\w. -]", "_", Path(value.replace("\\", "/")).name)[:120].strip(" .")
        or "download"
    )


def describe_action(action):
    # Do not duplicate typed text or credentials in the activity log.
    kind = action["type"]
    return {
        "click": "Clicked on the page",
        "double_click": "Double-clicked on the page",
        "move": "Moved the pointer",
        "scroll": "Scrolled the page",
        "type": "Typed text",
        "keypress": "Pressed a key",
        "drag": "Dragged on the page",
        "screenshot": "Observed the page",
        "wait": "Waited for the page",
    }[kind]


class BrowserDriver:
    def __init__(self, directory, *, headless=False, channel=None):
        self.directory = Path(directory)
        self.headless = headless
        self.channel = channel or (
            "msedge" if sys.platform == "win32" and not headless else None
        )
        self.downloads = []
        self.blocked = None

    def __enter__(self):
        from playwright.sync_api import sync_playwright

        self.directory.mkdir(parents=True, exist_ok=True)
        self.playwright = sync_playwright().start()
        try:
            self.browser = self.playwright.chromium.launch(
                headless=self.headless, channel=self.channel
            )
            self.context = self.browser.new_context(
                viewport={"width": WIDTH, "height": HEIGHT},
                accept_downloads=True,
                service_workers="block",
            )
            self.context.route("**/*", self._route)
            self.context.route_web_socket("**/*", lambda socket: socket.close())
            self.context.on("page", self._page_opened)
            self.page = self.context.new_page()
            self.page.set_default_timeout(10000)
            self.page.set_default_navigation_timeout(20000)
            return self
        except Exception:
            self.playwright.stop()
            raise

    def _route(self, route):
        try:
            public_url(route.request.url)
            route.continue_()
        except ValueError, OSError:
            route.abort()
            if route.request.is_navigation_request():
                self.blocked = "A local/private URL or unsupported address was blocked."

    def _page_opened(self, page):
        page.on("download", self._download)
        page.on("dialog", lambda dialog: self._dismiss(dialog))
        page.on("filechooser", lambda chooser: self._filechooser())
        if hasattr(self, "page") and page != self.page:
            # Keep one visible target. Ask the user to open pop-up destinations manually.
            self.blocked = "This site opened another tab. Pause and open the required page in the main browser tab."
            page.close()

    def _dismiss(self, dialog):
        self.blocked = "A website dialog needs your attention: " + dialog.message[:300]
        dialog.dismiss()

    def _filechooser(self):
        self.blocked = (
            "File upload needs you. This worker does not read files from your laptop."
        )

    def _download(self, download):
        if len(self.downloads) >= 20:
            download.cancel()
            self.blocked = "The 20-download limit was reached."
            return
        file_id = str(uuid4())
        name = safe_filename(download.suggested_filename)
        path = self.directory / file_id
        download.save_as(path)
        if path.stat().st_size > 50 * 1024 * 1024:
            path.unlink()
            self.blocked = "The download exceeded the 50 MB per-file limit."
            return
        self.downloads.append(
            {"id": file_id, "name": name, "bytes": path.stat().st_size}
        )

    def open_url(self, url):
        self.page.goto(public_url(url), wait_until="domcontentloaded")

    def screenshot(self):
        return self.page.screenshot(type="png", timeout=10000)

    def perform(self, action):
        kind = action["type"]
        points = action.get("path", []) or ([action] if "x" in action else [])
        if any(not (0 <= p["x"] < WIDTH and 0 <= p["y"] < HEIGHT) for p in points):
            raise BrowserActionError(
                "Muse returned coordinates outside the current viewport"
            )
        if kind == "click":
            button = {"wheel": "middle"}.get(action["button"], action["button"])
            if button not in {"left", "right", "middle"}:
                raise BrowserActionError(
                    "Browser back/forward mouse buttons are unsupported"
                )
            self.page.mouse.click(action["x"], action["y"], button=button)
        elif kind == "double_click":
            self.page.mouse.dblclick(action["x"], action["y"])
        elif kind == "move":
            self.page.mouse.move(action["x"], action["y"])
        elif kind == "scroll":
            self.page.mouse.move(action["x"], action["y"])
            self.page.mouse.wheel(action["scroll_x"], action["scroll_y"])
        elif kind == "type":
            self.page.keyboard.insert_text(action["text"])
        elif kind == "keypress":
            aliases = {
                "CTRL": "Control",
                "CMD": "Meta",
                "ALT": "Alt",
                "SHIFT": "Shift",
                "ENTER": "Enter",
                "RETURN": "Enter",
                "ESC": "Escape",
                "SPACE": "Space",
                "BACKSPACE": "Backspace",
                "TAB": "Tab",
                "ARROWUP": "ArrowUp",
                "ARROWDOWN": "ArrowDown",
                "ARROWLEFT": "ArrowLeft",
                "ARROWRIGHT": "ArrowRight",
            }
            keys = [aliases.get(k.upper(), k) for k in action["keys"]]
            allowed = {
                "Control",
                "Shift",
                "Enter",
                "Tab",
                "Space",
                "Backspace",
                "Delete",
                "Escape",
                "Home",
                "End",
                "PageUp",
                "PageDown",
                "ArrowUp",
                "ArrowDown",
                "ArrowLeft",
                "ArrowRight",
            }
            if any((len(k) != 1 and k not in allowed) or "+" in k for k in keys) or (
                "Control" in keys and keys[-1].lower() not in {"a", "z", "y"}
            ):
                raise BrowserActionError(
                    "This keyboard shortcut is unavailable in the dedicated browser"
                )
            self.page.keyboard.press("+".join(keys))
        elif kind == "drag":
            self.page.mouse.move(points[0]["x"], points[0]["y"])
            self.page.mouse.down()
            try:
                for point in points[1:]:
                    self.page.mouse.move(point["x"], point["y"])
            finally:
                self.page.mouse.up()
        elif kind == "wait":
            self.page.wait_for_timeout(700)
        elif kind != "screenshot":
            raise BrowserActionError("Unsupported computer action")
        # Dispatch browser events, including download and navigation callbacks.
        self.page.wait_for_timeout(150)

    def __exit__(self, *_):
        try:
            self.context.close()
            self.browser.close()
        finally:
            self.playwright.stop()
