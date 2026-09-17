"""Drive the real postcard.composer_window.PostcardComposerWindow end to end
against a live WebView2Gtk: builds the rich-text editor's WebView, waits for
its initial load, then exercises the same JS<->native round trip production
code depends on (evaluate_javascript via _exec, and the script-message
bridge via _on_editor_changed) instead of trusting the WebKitGTK-shaped API
surface matches without ever having actually called it.

Run against a built webview2-gtk lib/install-staging tree and this repo's
own gresource bundle, e.g.:
  just build
  PATH="../webview2-gtk/build/install-staging/bin:$PATH" \
  GI_TYPELIB_PATH="../webview2-gtk/build/install-staging/lib/girepository-1.0" \
  .venv/bin/python.exe tools/smoke_composer_window.py
"""

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebView2Gtk", "1.0")

sys.path.insert(0, "src")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

RESOURCE_PATH = "build/win/postcard.gresource"

# @Gtk.Template (in composer_window.py, evaluated at import time) needs the
# resource registered before that import runs -- must come before it, not
# just before app.run().
_resource = Gio.Resource.load(RESOURCE_PATH)
_resource._register()  # noqa: SLF001 -- GResource._register is the public entry point

from postcard.composer_window import PostcardComposerWindow  # noqa: E402
from postcard.core.store.database import Database  # noqa: E402


class _Check:
    """Waits for the editor's initial load-changed, types via
    evaluate_javascript, then waits for the resulting script-message round
    trip to update _body_html -- proof the JS bridge works both ways, not
    just that construction didn't raise."""

    def __init__(self, app: Gtk.Application) -> None:
        self.app = app
        self.failed: str | None = None
        self.stage = "initial_load"

        db = Database(":memory:")
        account = db.save_account(
            email="me@example.com",
            display_name="Me",
            imap_host="imap.example.com",
            imap_port=993,
            smtp_host="smtp.example.com",
            smtp_port=465,
        )

        self.composer = PostcardComposerWindow(app, db, account, subject="Test")
        self.composer.present()

        self.webview = self.composer._webview  # noqa: SLF001
        self.webview.connect("load-changed", self._on_load_changed)
        GLib.timeout_add(20000, self._on_timeout)

    def finish(self, ok: bool, message: str) -> None:
        if not ok:
            self.failed = message
        self.app.quit()

    def _on_timeout(self) -> bool:
        self.finish(False, "timed out waiting for the editor to finish loading")
        return GLib.SOURCE_REMOVE

    def _on_load_changed(self, _wv, load_event: int) -> None:
        import gi.repository

        webkit = gi.repository.WebView2Gtk
        if load_event != webkit.LoadEvent.FINISHED or self.stage != "initial_load":
            return
        self.stage = "typing"
        # evaluate_javascript is a synchronous COM call (ExecuteScript) --
        # calling it from directly inside this WebView2-originated signal
        # crashes the whole process with RPC_E_CANTCALLOUT_ININPUTSYNCCALL
        # (0x8001010D), a real COM reentrancy fault, not a Python exception.
        # GLib.idle_add defers it to a fresh mainloop iteration, off this
        # callback's stack -- same as production code always calling _exec
        # from a GTK button click, never from a WebView2 event handler.
        GLib.idle_add(self._type_into_editor)

    def _type_into_editor(self) -> bool:
        before = self.composer._body_html  # noqa: SLF001
        self.composer._exec("insertText", "hello from the smoke test")  # noqa: SLF001
        GLib.timeout_add(1500, self._check_after_typing, before)
        return GLib.SOURCE_REMOVE

    def _check_after_typing(self, before: str) -> bool:
        after = self.composer._body_html  # noqa: SLF001
        if after == before:
            self.finish(
                False,
                "_body_html did not change -- the JS<->native bridge is not working",
            )
        elif "hello from the smoke test" not in after:
            self.finish(False, f"typed text missing from _body_html: {after!r}")
        else:
            self.finish(True, "ok")
        return GLib.SOURCE_REMOVE


def main() -> int:
    Adw.init()
    app = Gtk.Application(application_id="dev.winpostcard.smoketest.composerwindow")
    checks: list[_Check] = []
    app.connect("activate", lambda app: checks.append(_Check(app)))
    app.run([])

    check = checks[0]
    if check.failed is not None:
        print(f"FAIL: {check.failed}", file=sys.stderr)
        return 1
    print("PASS: composer editor loads and the JS<->native round trip works")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
