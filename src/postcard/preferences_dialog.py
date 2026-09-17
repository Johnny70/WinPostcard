import logging
from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk

from .core import autostart
from .window_types import SETTING_SYNC_INTERVAL

logger = logging.getLogger(__name__)

# The sync-interval combo, in row order: the minute value stored in GSettings
# and the label shown for it. One list rather than two index-aligned ones, so a
# label can't drift from the value it describes. 0 = manual only.
SYNC_INTERVALS: tuple[tuple[int, str], ...] = (
    (0, _("Manually")),
    (5, _("Every 5 minutes")),
    (15, _("Every 15 minutes")),
    (30, _("Every 30 minutes")),
    (60, _("Every hour")),
)

# Used when the stored value isn't one of the offered intervals.
DEFAULT_SYNC_INTERVAL_MINUTES = 15

# The registry has no way to read back "did this actually take", so this key
# is our own record of what was last set.
SETTING_START_AT_LOGIN = "start-at-login"


@Gtk.Template(resource_path="/in/gxanshu/postcard/ui/preferences-dialog.ui")
class PostcardPreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "PostcardPreferencesDialog"

    notifications_row: Adw.SwitchRow = Gtk.Template.Child()
    images_row: Adw.SwitchRow = Gtk.Template.Child()
    avatars_row: Adw.SwitchRow = Gtk.Template.Child()
    account_names_row: Adw.SwitchRow = Gtk.Template.Child()
    background_row: Adw.SwitchRow = Gtk.Template.Child()
    autostart_row: Adw.SwitchRow = Gtk.Template.Child()
    interval_row: Adw.ComboRow = Gtk.Template.Child()
    signature_enabled_row: Adw.SwitchRow = Gtk.Template.Child()
    signature_view: Gtk.TextView = Gtk.Template.Child()

    def __init__(self, settings: Gio.Settings) -> None:
        super().__init__()
        self._settings = settings

        flags = Gio.SettingsBindFlags.DEFAULT
        settings.bind("notifications", self.notifications_row, "active", flags)
        settings.bind("load-remote-images", self.images_row, "active", flags)
        settings.bind("load-sender-avatars", self.avatars_row, "active", flags)
        settings.bind(
            "show-account-display-name", self.account_names_row, "active", flags
        )
        settings.bind("run-in-background", self.background_row, "active", flags)
        settings.bind("signature-enabled", self.signature_enabled_row, "active", flags)
        settings.bind(
            "signature-enabled",
            self.signature_view,
            "sensitive",
            Gio.SettingsBindFlags.GET,
        )

        self.interval_row.set_model(
            Gtk.StringList.new([label for _minutes, label in SYNC_INTERVALS])
        )
        self.interval_row.set_selected(
            self._interval_index(settings.get_int(SETTING_SYNC_INTERVAL))
        )
        self.interval_row.connect("notify::selected", self._on_interval_changed)

        self.autostart_row.set_active(settings.get_boolean(SETTING_START_AT_LOGIN))
        self.autostart_row.connect("notify::active", self._on_autostart_toggled)

        buffer = self.signature_view.get_buffer()
        buffer.set_text(settings.get_string("signature-text"))
        buffer.connect("changed", self._on_signature_changed)

    @staticmethod
    def _interval_index(minutes: int) -> int:
        """The combo row for a stored interval, falling back to the default."""
        offered = [value for value, _label in SYNC_INTERVALS]
        wanted = minutes if minutes in offered else DEFAULT_SYNC_INTERVAL_MINUTES
        return offered.index(wanted)

    def _on_interval_changed(self, row: Adw.ComboRow, _param: object) -> None:
        minutes, _label = SYNC_INTERVALS[row.get_selected()]
        self._settings.set_int(SETTING_SYNC_INTERVAL, minutes)

    def _on_signature_changed(self, buffer: Gtk.TextBuffer) -> None:
        start, end = buffer.get_bounds()
        self._settings.set_string("signature-text", buffer.get_text(start, end, False))

    def _on_autostart_toggled(self, row: Adw.SwitchRow, _param: object) -> None:
        is_wanted = row.get_active()
        if is_wanted == self._settings.get_boolean(SETTING_START_AT_LOGIN):
            return
        try:
            autostart.set_enabled(is_wanted)
        except OSError:
            logger.exception("could not update the autostart entry")
            row.set_active(self._settings.get_boolean(SETTING_START_AT_LOGIN))
            self.add_toast(
                Adw.Toast(
                    title=_("Could not change whether WinPostcard starts at login.")
                )
            )
            return
        self._settings.set_boolean(SETTING_START_AT_LOGIN, is_wanted)
