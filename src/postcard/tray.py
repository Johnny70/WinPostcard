"""A Windows tray icon (Shell_NotifyIcon, via pystray).

pystray runs its own Win32 message-loop thread, so every callback hops onto
the GTK main loop with GLib.idle_add before touching any Gio.Action/GObject
state -- confirmed safe in a spike (no deadlock, no race) recorded in
docs/devlog.json.

MODULE: postcard.tray
RESPONSIBILITY: the tray icon and its menu
DEPENDS ON: pystray, PIL (Pillow), .tray_actions
EXPOSES: Tray
"""

import logging
from collections.abc import Callable
from gettext import gettext as _
from pathlib import Path
from typing import TYPE_CHECKING

import pystray
from gi.repository import GLib

# Comes from the ucrt64 pacman package, not pip -- pyright's venv resolution
# does not follow pyvenv.cfg's include-system-site-packages for it, even
# though Pillow ships its own inline types (py.typed).
from PIL import Image, ImageDraw, ImageFont  # pyright: ignore[reportMissingImports]

from . import tray_actions

if TYPE_CHECKING:
    from gi.repository import Gtk

logger = logging.getLogger(__name__)

APP_ID = "in.gxanshu.postcard"
APP_NAME = "WinPostcard"

ICON_SIZE = 64
BADGE_RADIUS = 19
BADGE_RED = (224, 27, 36, 255)
BADGE_WHITE = (255, 255, 255, 255)
BADGE_FONT_SIZES = {1: 26, 2: 22, 3: 17}
MAX_BADGE_COUNT = 99

_MENU_ITEMS = (
    ("open", _("Open WinPostcard"), "app.focus-mail"),
    ("compose", _("Compose"), "win.compose"),
    ("refresh", _("Refresh Inbox"), "win.refresh"),
    ("quit", _("Quit"), "app.quit"),
)


def _icon_file() -> Path | None:
    for data_dir in GLib.get_system_data_dirs():
        path = Path(data_dir, "icons/hicolor/64x64/apps", f"{APP_ID}.png")
        if path.is_file():
            return path
    return None


def _base_image() -> Image.Image:
    icon_file = _icon_file()
    if icon_file is None:
        logger.warning("no %s.png on the system data dirs; using a placeholder", APP_ID)
        placeholder = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
        ImageDraw.Draw(placeholder).ellipse(
            (4, 4, ICON_SIZE - 4, ICON_SIZE - 4), fill=(53, 132, 228, 255)
        )
        return placeholder
    return Image.open(icon_file).convert("RGBA").resize((ICON_SIZE, ICON_SIZE))


def _badged_image(count: int) -> Image.Image:
    """The app icon with an unread bubble."""
    image = _base_image().copy()
    draw = ImageDraw.Draw(image)
    text = str(count) if count <= MAX_BADGE_COUNT else f"{MAX_BADGE_COUNT}+"
    center = ICON_SIZE - BADGE_RADIUS - 1
    draw.ellipse(
        (
            center - BADGE_RADIUS,
            center - BADGE_RADIUS,
            center + BADGE_RADIUS,
            center + BADGE_RADIUS,
        ),
        fill=BADGE_RED,
    )
    font = ImageFont.load_default(size=BADGE_FONT_SIZES[len(text)])
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = right - left, bottom - top
    draw.text(
        (center - text_width / 2 - left, center - text_height / 2 - top),
        text,
        fill=BADGE_WHITE,
        font=font,
    )
    return image


class Tray:
    def __init__(self, app: "Gtk.Application") -> None:
        self._app = app
        self._unread = 0
        self._icon = pystray.Icon(
            APP_ID,
            icon=_base_image(),
            title=APP_NAME,
            menu=pystray.Menu(
                *(
                    pystray.MenuItem(
                        label, self._handler(action), default=(key == "open")
                    )
                    for key, label, action in _MENU_ITEMS
                )
            ),
            visible=False,
        )

    def start(self) -> None:
        self._icon.run_detached()

    # run_detached() spawns pystray's Win32 message-loop thread as a plain,
    # non-daemon threading.Thread -- nothing else ever stops it. Left
    # uncalled, the process outlives every window and GTK's own shutdown,
    # invisible (no window, no tray icon if run-in-background is off) and
    # still holding a lock on the install directory, which is exactly what
    # the installer's CloseApplications=force then kills. stop() posts a
    # WM_STOP to the icon's own hidden window, so it is safe to call from
    # this (GTK main) thread even though the loop runs on another.
    def stop(self) -> None:
        self._icon.stop()

    def set_shown(self, is_shown: bool) -> None:
        self._icon.visible = is_shown

    def set_unread(self, count: int) -> None:
        if count == self._unread:
            return
        self._unread = count
        self._icon.icon = _badged_image(count) if count else _base_image()

    # pystray ships no type stubs, and pystray.Icon/MenuItem are resolved
    # dynamically per platform, so pyright cannot treat them as real types.
    def _handler(self, action: str) -> Callable[[object, object], None]:
        def on_click(_icon: object, _item: object) -> None:
            GLib.idle_add(self._activate, action)

        return on_click

    def _activate(self, action: str) -> bool:
        tray_actions.activate(self._app, action)
        return GLib.SOURCE_REMOVE
