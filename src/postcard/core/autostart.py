"""Launch on login, via a HKCU `...\\Run` registry value.

MODULE: postcard.core.autostart
RESPONSIBILITY: enabling/disabling launch-at-login
DEPENDS ON: winreg (stdlib, Windows-only, imported lazily so this module
  still imports on a non-Windows test runner)
EXPOSES: set_enabled
"""

import contextlib
import sys

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_VALUE_NAME = "WinPostcard"


def set_enabled(is_enabled: bool) -> None:
    """Write or remove the autostart registry value, raising OSError if that
    fails. Disabling an already-absent value is a no-op, not an error."""
    import winreg  # local: winreg does not exist off Windows

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
    except OSError as error:
        raise OSError(f"could not open HKCU\\{_RUN_KEY}") from error
    with key:
        if not is_enabled:
            with contextlib.suppress(FileNotFoundError):
                winreg.DeleteValue(key, _RUN_VALUE_NAME)
            return
        winreg.SetValueEx(key, _RUN_VALUE_NAME, 0, winreg.REG_SZ, _launch_command())


def _launch_command() -> str:
    # Points at the running interpreter until the app is packaged (a later
    # milestone) -- correct for a dev run, not yet for a real install.
    return f'"{sys.executable}" --hidden'
