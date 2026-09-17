from gi.repository import GLib

from postcard import tray


class _FakeApp:
    """A stand-in Adw.Application -- only used for identity checks here,
    since click routing itself is tray_actions' job and tested in
    tests/test_tray_actions.py."""


# --- icon construction -------------------------------------------------


def test_menu_has_the_four_actions_in_order(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    icon = tray.Tray(_FakeApp())

    labels = [item.text for item in icon._icon.menu.items]

    assert labels == ["Open WinPostcard", "Compose", "Refresh Inbox", "Quit"]


def test_the_open_entry_is_the_default_action(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    icon = tray.Tray(_FakeApp())

    defaults = [item.text for item in icon._icon.menu.items if item.default]

    assert defaults == ["Open WinPostcard"]


def test_starts_hidden(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    icon = tray.Tray(_FakeApp())

    assert icon._icon.visible is False


# --- start/set_shown/set_unread -----------------------------------------


def test_start_runs_the_icon_detached(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    calls = []
    icon = tray.Tray(_FakeApp())
    monkeypatch.setattr(icon._icon, "run_detached", lambda: calls.append(1))

    icon.start()

    assert calls == [1]


def test_set_shown_toggles_the_icon_visibility(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    icon = tray.Tray(_FakeApp())

    icon.set_shown(True)
    assert icon._icon.visible is True

    icon.set_shown(False)
    assert icon._icon.visible is False


def test_set_unread_is_a_noop_when_the_count_does_not_change(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    icon = tray.Tray(_FakeApp())
    unchanged = icon._icon.icon

    icon.set_unread(0)  # already 0 by default

    assert icon._icon.icon is unchanged


def test_set_unread_draws_a_badge_when_positive(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    badge_calls = []
    monkeypatch.setattr(
        tray, "_badged_image", lambda count: badge_calls.append(count) or "badged"
    )
    icon = tray.Tray(_FakeApp())

    icon.set_unread(5)

    assert badge_calls == [5]
    assert icon._icon.icon == "badged"


def test_set_unread_restores_the_plain_icon_at_zero(monkeypatch):
    monkeypatch.setattr(tray, "_base_image", lambda: "plain")
    monkeypatch.setattr(tray, "_badged_image", lambda _count: "badged")
    icon = tray.Tray(_FakeApp())
    assert icon._icon.icon == "plain"

    icon.set_unread(5)
    assert icon._icon.icon == "badged"

    icon.set_unread(0)
    assert icon._icon.icon == "plain"


# --- click routing --------------------------------------------------------


def test_a_menu_click_marshals_onto_the_main_loop_before_activating(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)
    app = _FakeApp()
    icon = tray.Tray(app)

    idle_calls = []
    monkeypatch.setattr(
        GLib, "idle_add", lambda func, *args: idle_calls.append((func, args))
    )
    activate_calls = []
    monkeypatch.setattr(
        tray.tray_actions,
        "activate",
        lambda target_app, action: activate_calls.append((target_app, action)),
    )

    compose_item = icon._icon.menu.items[1]
    assert compose_item.text == "Compose"
    compose_item(icon._icon)  # pystray's own way of firing a click

    assert activate_calls == []  # not yet -- still queued for the main loop
    assert len(idle_calls) == 1
    func, args = idle_calls[0]
    func(*args)  # simulate the main loop running the marshalled call
    assert activate_calls == [(app, "win.compose")]


# --- _base_image / _badged_image -----------------------------------------


def test_base_image_falls_back_to_a_placeholder_without_an_icon_file(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)

    image = tray._base_image()

    assert image.size == (tray.ICON_SIZE, tray.ICON_SIZE)


def test_badged_image_matches_the_base_image_size(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)

    image = tray._badged_image(7)

    assert image.size == (tray.ICON_SIZE, tray.ICON_SIZE)


def test_badged_image_collapses_the_count_above_the_max(monkeypatch):
    monkeypatch.setattr(tray, "_icon_file", lambda: None)

    # Would KeyError out of BADGE_FONT_SIZES if not collapsed to "99+".
    tray._badged_image(tray.MAX_BADGE_COUNT + 50)
