# Windows dev environment setup

WinPostcard has no Flatpak, so GTK4, libadwaita and PyGObject come from
[MSYS2](https://www.msys2.org/)'s UCRT64 packages instead of a from-source
build — `just init` (see the `justfile`) automates the steps below.

## HTML mail rendering: webview2-gtk fork

`composer_window.py` and `message_view.py` both need `WebKit` 6.0 on Linux,
which **has no Windows port** — it is Linux-only upstream. On Windows they
instead use `WebView2Gtk` (`from gi.repository import WebView2Gtk as WebKit`),
a fork of [webview2-gtk](https://github.com/roojs/webview2-gtk) (Microsoft
Edge WebView2) maintained at
[Johnny70/webview2-gtk](https://github.com/Johnny70/webview2-gtk), tracked
as its own separate repository (not vendored into this one — `git remote`
there has `origin` pointing at that fork and `upstream` at the original
`roojs/webview2-gtk`, so upstream fixes can still be pulled in). It adds
GObject-Introspection output (upstream ships none), makes navigation
blocking real (upstream's `PolicyDecision.ignore()`/`.use()` are documented
no-ops on Windows — security-critical for untrusted HTML mail, see
`scripts/smoke-navigation-block.py` there), and a few `WebViewSettings`
properties `message_view.py` needs. See that repo's own `docs/` for build
details.

The Python wiring (`gi.require_version`/imports/call sites) is done and the
app launches without an import error, but opening a real HTML message or the
compose window in a running app has not yet been manually verified — do
that before trusting this end to end.

## Prerequisites (one-time, `just init` + `just init-webview2gtk`)

1. **[MSYS2](https://www.msys2.org/)** (`winget install MSYS2.MSYS2`, default
   install path `C:\msys64`). Add `C:\msys64\usr\bin` and
   `C:\msys64\ucrt64\bin` to your `PATH` so `pacman`, `python.exe`,
   `blueprint-compiler` etc. are all reachable from a normal shell — this is
   MSYS2's own recommended post-install step, not specific to WinPostcard.
2. Run `just init`. It pacman-installs GTK4, libadwaita, PyGObject, pycairo,
   Pillow, blueprint-compiler and ruff (all as prebuilt UCRT64 packages — no
   compiling GTK from source), then creates `.venv` as a
   `--system-site-packages` venv against MSYS2's own Python so it can still
   see those pacman-installed packages, and pip-installs the handful of
   things MSYS2 does not package (`keyring`, `pystray`, `pyright`, `pytest`,
   `PyGObject-stubs`).
3. Clone [Johnny70/webview2-gtk](https://github.com/Johnny70/webview2-gtk)
   as a sibling directory next to this repo (`../webview2-gtk`), or point
   `WEBVIEW2GTK_DIR` at wherever you put it, then run
   `just init-webview2gtk` to build it. Re-run this whenever that repo's
   source changes — `just build`/`run`/`test` do not rebuild it themselves.

That's it — unlike a from-source GTK build, there is no MSVC, no vendored
SDK, and nothing to compile by hand. `just build`/`just run`/`just test` all
just need `ucrt64/bin` (and the webview2-gtk build output) on `PATH`, which
they add themselves.

## Running tests locally

`conftest.py` at the repo root adds `ucrt64/bin` to `PATH` automatically —
useful when running `pytest` directly (an editor/IDE run configuration)
instead of through `just test`, which already does this itself. It is a
no-op on Linux and a no-op on Windows too unless MSYS2 is installed at the
default location (or `UCRT64_DIR` points elsewhere).

## The tray icon

The Windows tray (`tray.py`, via `pystray`) is real and tested
(`tests/test_tray.py`). `pystray` runs its own Win32 message-loop thread;
every menu click hops onto the GTK main loop with `GLib.idle_add` before
touching any `Gio.Action`/GObject state, which a threading spike confirmed
is safe (see `docs/devlog.json`).

## History: why not gvsbuild?

An earlier version of this setup built GTK4/libadwaita from source via
[gvsbuild](https://github.com/wingtk/gvsbuild) against MSVC. That worked
(see `docs/devlog.json` for the journey — a `stdalign.h` shim, `--enable-gi`,
`vswhere.exe` on `PATH`, a `NoDefaultCurrentDirectoryInExePath` gotcha), but
turned out to be the wrong foundation once HTML mail rendering needed
`webview2-gtk`: that project builds against MSYS2 UCRT64 (MinGW), and a
MinGW-built GTK4 cannot safely share a process with an MSVC-built one —
GObject's type system is a single global registry inside `glib`'s own DLL,
so two separately-built copies of it in one process is a correctness
problem, not just an inconvenience. Switching the whole toolchain to MSYS2
UCRT64 (this page) fixed that at the root, and turned out simpler besides:
prebuilt packages instead of an hours-long source build.
