import keyring.errors

from postcard.core import secrets
from postcard.core.models.account import Account
from postcard.core.net.auth import Credential


def account(**overrides) -> Account:
    fields = {
        "id": 1,
        "email": "ada@example.com",
        "display_name": "Ada",
        "imap_host": "imap.example.com",
        "imap_port": 993,
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
    }
    return Account(**(fields | overrides))


# --- store/lookup/clear_password -----------------------------------------


def test_store_password_uses_the_service_and_account_id(monkeypatch):
    calls = []
    monkeypatch.setattr(
        secrets.keyring,
        "set_password",
        lambda service, username, password: calls.append((service, username, password)),
    )

    secrets.store_password(42, "hunter2")

    assert calls == [(secrets._SERVICE, "42", "hunter2")]


def test_lookup_password_returns_the_stored_value(monkeypatch):
    monkeypatch.setattr(
        secrets.keyring,
        "get_password",
        lambda _service, username: f"secret-for-{username}",
    )

    assert secrets.lookup_password(42) == "secret-for-42"


def test_lookup_password_returns_none_on_a_keyring_error(monkeypatch):
    def raise_error(*_args):
        raise keyring.errors.KeyringError("backend unavailable")

    monkeypatch.setattr(secrets.keyring, "get_password", raise_error)

    assert secrets.lookup_password(1) is None


def test_clear_password_returns_false_when_nothing_was_stored(monkeypatch):
    def raise_error(*_args):
        raise keyring.errors.PasswordDeleteError("not found")

    monkeypatch.setattr(secrets.keyring, "delete_password", raise_error)

    assert secrets.clear_password(1) is False


def test_clear_password_returns_true_on_success(monkeypatch):
    monkeypatch.setattr(secrets.keyring, "delete_password", lambda *_a: None)

    assert secrets.clear_password(1) is True


# --- credential_for -------------------------------------------------------


def test_credential_for_asks_the_secret_store(monkeypatch):
    monkeypatch.setattr(
        secrets, "lookup_password", lambda account_id: f"pw-{account_id}"
    )

    result = secrets.credential_for(account(id=7))

    assert result == Credential("ada@example.com", "pw-7")


def test_credential_for_returns_none_without_a_stored_password(monkeypatch):
    monkeypatch.setattr(secrets, "lookup_password", lambda _account_id: None)

    assert secrets.credential_for(account()) is None


def test_credential_for_uses_the_username_override_when_set(monkeypatch):
    monkeypatch.setattr(secrets, "lookup_password", lambda _account_id: "pw")

    result = secrets.credential_for(account(username="lovelace.a"))

    assert result == Credential("lovelace.a", "pw")
