from gi.repository import Adw, GObject, Gtk

from .core.models.folder import Folder
from .core.store.database import Database
from .mail_sync import OUTBOX_FOLDER


@Gtk.Template(resource_path="/in/gxanshu/postcard/ui/rule-dialog.ui")
class PostcardRuleDialog(Adw.Dialog):
    __gtype_name__ = "PostcardRuleDialog"

    cancel_button: Gtk.Button = Gtk.Template.Child()
    add_button: Gtk.Button = Gtk.Template.Child()
    sender_row: Adw.EntryRow = Gtk.Template.Child()
    folder_row: Adw.ComboRow = Gtk.Template.Child()

    # Carries the new/repointed rule's id, so a listener can apply it to
    # mail that already arrived before the rule existed.
    __gsignals__ = {
        "rule-added": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, db: Database, account_id: int) -> None:
        super().__init__()
        self._db = db
        self._account_id = account_id
        # Outbox is a local-only holding folder, never a real IMAP mailbox --
        # nothing can be moved into it by a rule.
        self._folders: list[Folder] = [
            folder
            for folder in db.folders_for_account(account_id)
            if folder.name != OUTBOX_FOLDER
        ]
        self.folder_row.set_model(
            Gtk.StringList(strings=[folder.name for folder in self._folders])
        )

        self.cancel_button.connect("clicked", lambda _b: self.close())
        self.add_button.connect("clicked", self._on_add_clicked)
        self.sender_row.connect("changed", self._update_add_sensitivity)
        self._update_add_sensitivity()

    def _update_add_sensitivity(self, *_args: object) -> None:
        sender = self.sender_row.get_text().strip()
        self.add_button.set_sensitive("@" in sender and bool(self._folders))

    def _on_add_clicked(self, _button: Gtk.Button) -> None:
        folder = self._folders[self.folder_row.get_selected()]
        rule = self._db.save_rule(
            self._account_id,
            self.sender_row.get_text().strip().lower(),
            folder.id,
        )
        self.emit("rule-added", rule.id)
        self.close()
