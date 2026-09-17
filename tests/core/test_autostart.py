import re
import sys

import pytest

from postcard.core import autostart


class _FakeWinReg:
    """Stands in for the winreg module -- real calls would touch the actual
    Windows registry, which tests must never do."""

    HKEY_CURRENT_USER = "HKCU"
    KEY_SET_VALUE = 1
    REG_SZ = 1

    def __init__(self, *, open_fails: bool = False, existing: dict | None = None):
        self._open_fails = open_fails
        self._values = dict(existing or {})
        self.written: list[tuple[str, str]] = []
        self.deleted: list[str] = []

    def OpenKey(self, _hive, _path, _reserved, _access):
        if self._open_fails:
            raise OSError("access denied")
        return self

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def SetValueEx(self, _key, name, _reserved, _type, value):
        self._values[name] = value
        self.written.append((name, value))

    def DeleteValue(self, _key, name):
        if name not in self._values:
            raise FileNotFoundError(name)
        del self._values[name]
        self.deleted.append(name)


def test_set_enabled_true_writes_the_launch_command(monkeypatch):
    fake = _FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    autostart.set_enabled(True)

    assert fake.written == [(autostart._RUN_VALUE_NAME, f'"{sys.executable}" --hidden')]


def test_set_enabled_false_deletes_the_value(monkeypatch):
    fake = _FakeWinReg(existing={autostart._RUN_VALUE_NAME: "whatever"})
    monkeypatch.setitem(sys.modules, "winreg", fake)

    autostart.set_enabled(False)

    assert fake.deleted == [autostart._RUN_VALUE_NAME]


def test_set_enabled_false_when_already_absent_does_not_raise(monkeypatch):
    fake = _FakeWinReg()
    monkeypatch.setitem(sys.modules, "winreg", fake)

    autostart.set_enabled(False)


def test_set_enabled_wraps_a_failure_to_open_the_key(monkeypatch):
    fake = _FakeWinReg(open_fails=True)
    monkeypatch.setitem(sys.modules, "winreg", fake)

    with pytest.raises(OSError, match=re.escape(autostart._RUN_KEY)):
        autostart.set_enabled(True)
