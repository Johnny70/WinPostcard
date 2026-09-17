"""Which app.- or win.-scoped Gio.Action a tray click should run. Shared
between tray.py's D-Bus StatusNotifierItem on Linux and
core/platform/windows_tray.py's pystray icon on Windows, since both let the
same four menu entries (Open, Compose, Refresh, Quit) drive the same
Adw.Application actions."""

from typing import TYPE_CHECKING

from gi.repository import Gio

if TYPE_CHECKING:
    from gi.repository import Gtk


def activate(app: "Gtk.Application", action: str) -> None:
    scope, _sep, name = action.partition(".")
    if scope == "app":
        target = app
    else:
        # A hidden window still answers its actions, so only build one when
        # there is none. Refreshing from the tray should not pop it open.
        target = _action_window(app)
        if target is None:
            app.activate()
            target = _action_window(app)
    found = target.lookup_action(name) if target is not None else None
    if found is not None:
        found.activate(None)


# Only the main window has actions; a composer is a plain Adw.Window.
def _action_window(app: "Gtk.Application") -> Gio.ActionMap | None:
    return next((w for w in app.get_windows() if isinstance(w, Gio.ActionMap)), None)
