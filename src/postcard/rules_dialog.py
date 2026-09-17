from gettext import gettext as _

from gi.repository import Adw, GObject, Gtk

from .core.models.account import Account
from .core.store.database import Database
from .rule_dialog import PostcardRuleDialog


@Gtk.Template(resource_path="/in/gxanshu/postcard/ui/rules-dialog.ui")
class PostcardRulesDialog(Adw.Dialog):
    __gtype_name__ = "PostcardRulesDialog"

    rules_group: Adw.PreferencesGroup = Gtk.Template.Child()
    add_button: Gtk.Button = Gtk.Template.Child()

    # Relayed from PostcardRuleDialog's own "rule-added" -- the window is
    # what can actually apply a rule to mail already sitting in the inbox
    # (it owns the account-move worker machinery this dialog has no access
    # to), so this just passes the new rule's id up to whoever opened us.
    __gsignals__ = {
        "rule-created": (GObject.SignalFlags.RUN_FIRST, None, (int,)),
    }

    def __init__(self, db: Database, account: Account) -> None:
        super().__init__()
        self._db = db
        self._account = account
        self._rows: list[Adw.ActionRow] = []

        self.set_title(_("Rules — {email}").format(email=account.email))
        self.add_button.connect("clicked", self._on_add_clicked)
        self._reload()

    def _reload(self) -> None:
        for row in self._rows:
            self.rules_group.remove(row)
        self._rows.clear()

        for rule in self._db.rules_for_account(self._account.id):
            folder = self._db.get_folder(rule.folder_id)
            folder_name = folder.name if folder is not None else "?"
            row = Adw.ActionRow(
                title=rule.sender_address,
                subtitle=_("Move to {folder}").format(folder=folder_name),
            )

            remove_button = Gtk.Button(
                icon_name="user-trash-symbolic",
                valign=Gtk.Align.CENTER,
                tooltip_text=_("Remove Rule"),
            )
            remove_button.add_css_class("flat")
            remove_button.connect("clicked", self._on_remove_clicked, rule.id)
            row.add_suffix(remove_button)

            self.rules_group.add(row)
            self._rows.append(row)

    def _on_remove_clicked(self, _button: Gtk.Button, rule_id: int) -> None:
        self._db.delete_rule(rule_id)
        self._reload()

    def _on_add_clicked(self, _button: Gtk.Button) -> None:
        dialog = PostcardRuleDialog(self._db, self._account.id)
        dialog.connect("rule-added", self._on_rule_added)
        dialog.present(self)

    def _on_rule_added(self, _dialog: PostcardRuleDialog, rule_id: int) -> None:
        self._reload()
        self.emit("rule-created", rule_id)
