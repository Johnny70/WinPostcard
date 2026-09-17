# WinPostcard — task runner
# Run `just` with no args to see all recipes.
#
# WinPostcard is a Windows app: GTK4, libadwaita and PyGObject come from
# MSYS2's UCRT64 packages (there is no other system package manager for GTK
# on Windows). See docs/windows-setup.md for the one-time MSYS2 setup.
#
#   just init              (one time)  pacman-install the GTK4/libadwaita/
#                                      PyGObject stack and create the dev venv
#   just init-webview2gtk  (one time, and after that repo's source changes)
#                                      build the webview2-gtk fork (HTML mail)
#   just build                        compile blueprints -> gresource -> gschema
#   just run                          build, then launch WinPostcard from source

# A plain host meson build dir, used ONLY by `pot` to regenerate translations.
builddir := "build"

# Unix-style, not "C:/..." -- Git Bash mis-splits a drive-letter colon when
# this gets joined into a colon-separated $PATH below, so every recipe below
# builds paths from this instead of hardcoding "C:/...". MSYS auto-converts
# it back to a real Windows path when spawning python.exe, blueprint-compiler
# etc.
ucrt64-dir := env_var_or_default("UCRT64_DIR", "/c/msys64/ucrt64")
python := if path_exists(".venv/bin/python.exe") == "true" { ".venv/bin/python.exe" } else { "python" }

# webview2-gtk (HTML mail rendering/composing) is a separate fork/repo, not
# part of this one -- see docs/devlog.json. Default: a sibling checkout.
webview2gtk-dir := env_var_or_default("WEBVIEW2GTK_DIR", "../webview2-gtk")
webview2gtk-stage := webview2gtk-dir / "build/install-staging"

# Show the recipe list (default when you just run `just`).
default:
    @just --list

# ----------------------------------------------------------------------------
# First-time setup
# ----------------------------------------------------------------------------

# One-time: pacman-install GTK4 + libadwaita + PyGObject + blueprint-compiler
# (all as prebuilt MSYS2 UCRT64 packages -- no compiling GTK from source),
# and create the dev venv. Needs MSYS2 first, with its usr/bin and ucrt64/bin
# on PATH -- see docs/windows-setup.md.
init:
    #!/usr/bin/env bash
    set -euo pipefail
    pacman -S --needed --noconfirm \
        mingw-w64-ucrt-x86_64-gtk4 \
        mingw-w64-ucrt-x86_64-libadwaita \
        mingw-w64-ucrt-x86_64-python-gobject \
        mingw-w64-ucrt-x86_64-python-cairo \
        mingw-w64-ucrt-x86_64-python-pillow \
        mingw-w64-ucrt-x86_64-blueprint-compiler \
        mingw-w64-ucrt-x86_64-ruff \
        mingw-w64-ucrt-x86_64-python-pip
    # --system-site-packages: gi/cairo/PIL/ruff come from the pacman packages
    # above, not pip -- pip only needs to add what MSYS2 does not package.
    "{{ucrt64-dir}}/bin/python.exe" -m venv --clear --system-site-packages .venv
    .venv/bin/python.exe -m pip install keyring pystray pyright pytest pyinstaller
    .venv/bin/python.exe -m pip install --no-deps PyGObject-stubs

# Build webview2-gtk (HTML mail rendering/composing) from its own repo,
# checked out as a sibling directory -- see WEBVIEW2GTK_DIR above. Separate
# from `init` since it needs that repo to exist first and takes real compile
# time; re-run this whenever that repo's source changes.
init-webview2gtk:
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="{{ucrt64-dir}}/bin:$PATH"
    if [ ! -d "{{webview2gtk-dir}}" ]; then
        echo "init-webview2gtk: {{webview2gtk-dir}} not found (set WEBVIEW2GTK_DIR or clone it there)" >&2
        exit 1
    fi
    bash "{{webview2gtk-dir}}/scripts/wv2gtk-build.sh" lib \
        "{{webview2gtk-dir}}/build" "{{webview2gtk-stage}}" \
        "{{webview2gtk-dir}}/build/libwebview2gtk-1.stamp"

# ----------------------------------------------------------------------------
# Build & run
# ----------------------------------------------------------------------------

# Compile blueprints -> gresource -> gschema. There is no Flatpak sandbox to
# build inside, so this is the standalone equivalent of what meson's
# gnome.compile_resources() + install did there.
build:
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="{{ucrt64-dir}}/bin:$PATH"
    mkdir -p build/win
    # blueprint-compiler infers each output's ui/ subdirectory from its input
    # path relative to the base dir given here -- src, not src/ui, is what
    # makes each .ui land at build/win/ui/ instead of build/win/, which is
    # where postcard.gresource.xml expects to find it.
    blueprint-compiler batch-compile build/win src src/ui/*.blp
    # Untranslated stand-in for the .metainfo.xml meson's i18n.merge_file()
    # would produce at a real build. Must exist before glib-compile-resources
    # runs: postcard.gresource.xml references it.
    cp data/in.gxanshu.postcard.metainfo.xml.in build/win/in.gxanshu.postcard.metainfo.xml
    glib-compile-resources --sourcedir=src --sourcedir=build/win \
        --target=build/win/postcard.gresource src/postcard.gresource.xml
    mkdir -p build/win/glib-2.0/schemas
    cp data/in.gxanshu.postcard.gschema.xml build/win/glib-2.0/schemas/
    glib-compile-schemas build/win/glib-2.0/schemas

# Build, then launch WinPostcard from source. tools/win_run.py mirrors
# postcard.in's own resource-loading.
run: build
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="{{webview2gtk-stage}}/bin:{{ucrt64-dir}}/bin:$PATH"
    export GI_TYPELIB_PATH="{{webview2gtk-stage}}/lib/girepository-1.0"
    export PYTHONPATH="src"
    export GSETTINGS_SCHEMA_DIR="build/win/glib-2.0/schemas"
    "{{python}}" tools/win_run.py

# Run with verbose GLib logging (handy for debugging signals/lifecycle).
run-debug: build
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="{{webview2gtk-stage}}/bin:{{ucrt64-dir}}/bin:$PATH"
    export GI_TYPELIB_PATH="{{webview2gtk-stage}}/lib/girepository-1.0"
    export PYTHONPATH="src"
    export GSETTINGS_SCHEMA_DIR="build/win/glib-2.0/schemas"
    export G_MESSAGES_DEBUG=all
    "{{python}}" tools/win_run.py

# Build a standalone build/pkg-dist/WinPostcard/WinPostcard.exe -- no MSYS2,
# no terminal, no `just run` needed to launch it afterward. Needs `just
# init-webview2gtk` done at least once first.
package: build
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="{{ucrt64-dir}}/bin:$PATH"
    "{{python}}" tools/win_package.py

# Build build/pkg-installer/WinPostcard-Setup.exe -- a per-user installer
# (Start Menu shortcut, optional desktop icon, uninstaller), no admin rights
# needed. Needs Inno Setup 6 (winget install JRSoftware.InnoSetup).
installer: package
    #!/usr/bin/env bash
    set -euo pipefail
    iscc="$LOCALAPPDATA/Programs/Inno Setup 6/ISCC.exe"
    if [[ ! -f "$iscc" ]]; then
        echo "installer: Inno Setup not found at $iscc -- winget install JRSoftware.InnoSetup" >&2
        exit 1
    fi
    "$iscc" packaging/WinPostcard.iss

# ----------------------------------------------------------------------------
# Website
# ----------------------------------------------------------------------------

# Build web/ into build/site and serve it at http://localhost:8000 (Ctrl+C stops).
site port="8000":
    sh web/build.sh "{{builddir}}/site"
    @echo "Serving http://localhost:{{port}}"
    {{python}} -m http.server {{port}} -d "{{builddir}}/site"

# ----------------------------------------------------------------------------
# Editor tooling & housekeeping
# ----------------------------------------------------------------------------

# Format the codebase with ruff.
fmt:
    ruff format src tests tools

# Lint, format-check and type-check the Python source. Enforces
# .claude/skills/coding-standards — see [tool.ruff.lint] in pyproject.toml.
check:
    ruff check src tests tools
    ruff format --check src tests tools
    {{python}} -m pyright src/postcard

# Run the test suite against the UCRT64 GTK stack (see docs/windows-setup.md).
test *ARGS: check
    #!/usr/bin/env bash
    set -euo pipefail
    export PATH="{{webview2gtk-stage}}/bin:{{ucrt64-dir}}/bin:$PATH"
    export GI_TYPELIB_PATH="{{webview2gtk-stage}}/lib/girepository-1.0"
    "{{python}}" -m pytest {{ARGS}}

# Regenerate the .pot translation template. Opt-in dev tool: needs `meson`,
# `ninja`, and `gettext` on the host (not required for `build`/`run`).
pot:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ ! -d "{{builddir}}" ]; then
        meson setup "{{builddir}}"
    else
        meson setup --reconfigure "{{builddir}}"
    fi
    ninja -C "{{builddir}}" postcard-pot

# Remove all build artifacts.
clean:
    rm -rf "{{builddir}}"
