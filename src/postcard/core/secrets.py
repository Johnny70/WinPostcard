"""Storing and retrieving an account's password in the Windows Credential
Manager, via the `keyring` package.

MODULE: postcard.core.secrets
RESPONSIBILITY: account password storage and sign-in credential lookup
DEPENDS ON: keyring, .models.account, .net.auth
EXPOSES: store_password, lookup_password, clear_password, credential_for
"""

import logging

import keyring
import keyring.errors

from .models.account import Account
from .net.auth import Credential

logger = logging.getLogger(__name__)

_SERVICE = "in.gxanshu.postcard"


def store_password(account_id: int, password: str) -> None:
    keyring.set_password(_SERVICE, str(account_id), password)


def lookup_password(account_id: int) -> str | None:
    try:
        return keyring.get_password(_SERVICE, str(account_id))
    except keyring.errors.KeyringError:
        logger.exception(
            "could not read account %d from Windows Credential Manager", account_id
        )
        return None


def clear_password(account_id: int) -> bool:
    try:
        keyring.delete_password(_SERVICE, str(account_id))
    except keyring.errors.PasswordDeleteError:
        # Nothing was stored for this account: a normal False, not an error.
        return False
    return True


def credential_for(account: Account) -> Credential | None:
    """How to sign this account in, or None when we cannot."""
    password = lookup_password(account.id)
    return Credential(account.login_name, password) if password else None
