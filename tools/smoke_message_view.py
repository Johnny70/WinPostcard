"""Drive the real postcard.message_view.MessageView end to end against a live
WebView2Gtk, instead of trusting that WebKitGTK-shaped code "just works" on
WebView2. This caught two real bugs on first use, neither visible from
reading the code or from pytest's mocked-dependency unit tests:

- WebView2's NavigateToString (what load_html() uses) fires
  NavigationStarting for its own generated data:text/html;... document.
  WebKitGTK's load_html() instead arrives as about:blank. The original
  blocking logic treated that as a hostile navigation and silently killed
  every HTML message's own render.
- The "Show Images" reload path (a second load_html() call reusing the
  fix above) had the same problem, because the fix was applied to the
  first load_html() call site but not this one.

Run against a built webview2-gtk lib/install-staging tree, e.g.:
  PATH="../webview2-gtk/build/install-staging/bin:$PATH" \
  GI_TYPELIB_PATH="../webview2-gtk/build/install-staging/lib/girepository-1.0" \
  .venv/bin/python.exe tools/smoke_message_view.py
"""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebView2Gtk", "1.0")

sys.path.insert(0, "src")

from gi.repository import Adw, GLib, Gtk  # noqa: E402
from gi.repository import (  # noqa: E402
    WebView2Gtk as WebKit,  # pyright: ignore[reportAttributeAccessIssue]
)

from postcard import message_view  # noqa: E402
from postcard.core.models.email import Email  # noqa: E402

BLOCKED_URL = "https://example.invalid/blocked-target"
_LINK = b'<a href="' + BLOCKED_URL.encode() + b'">click</a>'
RAW = (
    b"From: Eve <eve@example.com>\n"
    b"Subject: Test\n"
    b"MIME-Version: 1.0\n"
    b'Content-Type: text/html; charset="utf-8"\n\n'
    b"<html><body><p>hi</p>" + _LINK + b"</body></html>\n"
)


def on_load(_email: Email, callback) -> None:
    callback(RAW, None)


def on_save_attachment(_a: object) -> None:
    pass


def on_open_attachment(_a: object) -> None:
    pass


def on_unsubscribe(_target: object, _hide: object) -> None:
    pass


class _Check:
    """Drives one MessageView through: initial render, a blocked navigation
    attempt, then a Show Images reload -- each step gated on the real
    WebView's load-changed signal, not a fixed sleep."""

    def __init__(self, app: Gtk.Application) -> None:
        self.app = app
        self.failed: str | None = None
        self.stage = "initial_load"

        window = Gtk.ApplicationWindow(application=app)
        window.set_default_size(640, 480)
        email = Email(
            id=1,
            folder_id=1,
            server_id="1",
            sender="Eve",
            subject="Test",
            preview="",
            date="",
            is_unread=False,
        )
        self.view = message_view.MessageView(
            email,
            on_load,
            on_save_attachment,
            on_open_attachment,
            on_unsubscribe,
            is_expanded=True,
        )
        window.set_child(self.view)
        window.present()

        self.webview: WebKit.WebView | None = self.view._webview  # noqa: SLF001
        if self.webview is None:
            self.finish(False, "MessageView._show_html did not create a WebView")
            return
        self.webview.connect("load-changed", self._on_load_changed)
        GLib.timeout_add(20000, self._on_timeout)

    def finish(self, ok: bool, message: str) -> None:
        if not ok:
            self.failed = message
        self.app.quit()

    def _on_timeout(self) -> bool:
        self.finish(False, "timed out waiting for the WebView to finish loading")
        return GLib.SOURCE_REMOVE

    def _on_load_changed(self, _wv: WebKit.WebView, load_event: int) -> None:
        assert self.webview is not None
        if load_event != WebKit.LoadEvent.FINISHED or self.stage != "initial_load":
            return
        self.stage = "navigating"
        self.webview.load_uri(BLOCKED_URL)
        GLib.timeout_add(1500, self._check_after_blocked_attempt)

    def _check_after_blocked_attempt(self) -> bool:
        assert self.webview is not None
        if self.webview.get_uri() == BLOCKED_URL:
            self.finish(False, "webview navigated to the blocked URL")
            return GLib.SOURCE_REMOVE
        banner = self.view._images_banner  # noqa: SLF001
        if banner is None:
            self.finish(False, "no remote-images banner was shown")
            return GLib.SOURCE_REMOVE
        self.stage = "reload_after_show_images"
        self.view._on_show_images_clicked(banner)  # noqa: SLF001
        GLib.timeout_add(1500, self._check_after_reload)
        return GLib.SOURCE_REMOVE

    def _check_after_reload(self) -> bool:
        assert self.webview is not None
        if self.webview.get_uri() == BLOCKED_URL:
            self.finish(False, "webview navigated to the blocked URL after the reload")
        else:
            self.finish(True, "ok")
        return GLib.SOURCE_REMOVE


def main() -> int:
    Adw.init()
    app = Gtk.Application(application_id="dev.winpostcard.smoketest.messageview")
    checks: list[_Check] = []
    app.connect("activate", lambda app: checks.append(_Check(app)))
    app.run([])

    check = checks[0]
    if check.failed is not None:
        print(f"FAIL: {check.failed}", file=sys.stderr)
        return 1
    print("PASS: MessageView renders, blocks a link nav, and Show Images still renders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
