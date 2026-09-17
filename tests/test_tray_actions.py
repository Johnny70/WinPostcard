from gi.repository import Gio

from postcard import tray_actions


def _action_map_with(name: str, on_activate) -> Gio.SimpleActionGroup:
    """A Gio.ActionMap (as a real window would be) with one action wired up."""
    group = Gio.SimpleActionGroup()
    action = Gio.SimpleAction.new(name, None)
    action.connect("activate", on_activate)
    group.add_action(action)
    return group


class _FakeApp:
    def __init__(self, windows: list[object]) -> None:
        self._windows = windows
        self.activated = False

    def get_windows(self) -> list[object]:
        return self._windows

    def activate(self) -> None:
        self.activated = True


def test_app_scope_runs_the_action_on_the_application():
    calls = []
    app = _FakeApp([])
    app.lookup_action = _action_map_with(
        "quit", lambda *_: calls.append("quit")
    ).lookup_action

    tray_actions.activate(app, "app.quit")

    assert calls == ["quit"]


def test_win_scope_runs_the_action_on_the_open_window():
    calls = []
    window = _action_map_with("compose", lambda *_: calls.append("compose"))
    app = _FakeApp([window])

    tray_actions.activate(app, "win.compose")

    assert calls == ["compose"]
    assert app.activated is False


def test_win_scope_opens_the_app_when_no_window_exists():
    app = _FakeApp([])

    tray_actions.activate(app, "win.compose")

    assert app.activated is True


def test_win_scope_ignores_a_window_that_is_not_an_action_map():
    app = _FakeApp([object()])

    tray_actions.activate(app, "win.compose")  # must not raise

    assert app.activated is True
