# Contributing to WinPostcard

Thanks for taking a look! This covers how to get a dev environment running.
For the project's architecture and conventions, see [CLAUDE.md](CLAUDE.md).

## Setup

WinPostcard is a Windows app. GTK 4, libadwaita and PyGObject come from
[MSYS2](https://www.msys2.org/)'s UCRT64 packages. See
[docs/windows-setup.md](docs/windows-setup.md) first for the one-time MSYS2
setup.

```bash
just init      # one-time: pacman-install GTK4/libadwaita/PyGObject via MSYS2
just run       # build from your working tree and launch it — the normal dev loop
```

`just init` only needs to run once per machine. After that, `just run` is the
loop: it rebuilds from whatever is in your working tree and launches the app.

A few more recipes worth knowing:

```bash
just build     # compile blueprints -> gresource -> gschema, without launching
just run-debug # run with G_MESSAGES_DEBUG=all
just check     # ruff check + ruff format --check + pyright
just test      # run the test suite (also runs `check` first)
just fmt       # auto-format with ruff
```

Run `just` with no arguments any time to see the full recipe list.

## Before you submit

Code contributions should pass `just check` and `just test` — CI runs the
same checks.
