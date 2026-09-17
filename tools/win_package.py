"""Builds a standalone `dist/WinPostcard/WinPostcard.exe` via PyInstaller --
no MSYS2, no `just init`, no terminal needed to run it afterward.

Assumes `just build` already produced build/win/postcard.gresource and
build/win/glib-2.0/schemas/, and that webview2-gtk is built (WEBVIEW2GTK_DIR,
default ../webview2-gtk). PyInstaller's own binary dependency walker finds
the ucrt64 GTK/Adw DLLs automatically from PATH, but its gi hooks hardcode
GTK 3.0 with no override for a GTK4 app, so they find none of the actual
.typelib files -- this script stages every ucrt64 typelib itself, plus the
things PyInstaller's hooks never knew to look for at all: this app's own
gresource, a merged GSettings schema (ours + GTK/Adw's own), the Adwaita icon
theme, gdk-pixbuf loaders (with their cache file regenerated to point at the
staged copy, since the original bakes in absolute C:\\msys64\\... paths), and
webview2-gtk's own typelib/DLL (a separate build entirely).
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UCRT64 = Path(os.environ.get("UCRT64_DIR", r"C:\msys64\ucrt64"))
WEBVIEW2GTK_STAGE = (
    Path(os.environ.get("WEBVIEW2GTK_DIR", ROOT.parent / "webview2-gtk"))
    / "build"
    / "install-staging"
)
STAGE = ROOT / "build" / "pkg-stage"
DIST = ROOT / "build" / "pkg-dist"
WORK = ROOT / "build" / "pkg-work"


def _require(path: Path, made_by: str) -> None:
    if not path.exists():
        print(f"win_package: missing {path} -- run {made_by} first", file=sys.stderr)
        sys.exit(1)


def _stage_schemas() -> None:
    schemas_dir = STAGE / "glib-2.0" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    for xml in (UCRT64 / "share" / "glib-2.0" / "schemas").glob("*.xml"):
        shutil.copy2(xml, schemas_dir)
    shutil.copy2(ROOT / "data" / "in.gxanshu.postcard.gschema.xml", schemas_dir)
    subprocess.run(["glib-compile-schemas", str(schemas_dir)], check=True)


def _stage_pixbuf_loaders() -> None:
    src = UCRT64 / "lib" / "gdk-pixbuf-2.0" / "2.10.0"
    dst = STAGE / "lib" / "gdk-pixbuf-2.0" / "2.10.0"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src / "loaders", dst / "loaders")
    loader_dlls = sorted(str(p) for p in (dst / "loaders").glob("*.dll"))
    cache = subprocess.run(
        ["gdk-pixbuf-query-loaders", *loader_dlls],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    (dst / "loaders.cache").write_text(cache, encoding="utf-8")


def _stage_typelibs() -> None:
    # PyInstaller's own gi hooks (hook-gi.repository.Gtk.py etc.) hardcode
    # GiModuleInfo('Gtk', '3.0') -- there is no override for a GTK4 app, so
    # they silently fail to find our Gtk-4.0/Gdk-4.0/etc. typelibs at all
    # (confirmed: the DLLs still get bundled via the generic binary
    # dependency walker, only the .typelib files are missing). Stage every
    # ucrt64 typelib ourselves instead of trusting that hook, same as
    # webview2-gtk's (a separate build those hooks know nothing about
    # regardless).
    typelib_dir = STAGE / "lib" / "girepository-1.0"
    typelib_dir.mkdir(parents=True, exist_ok=True)
    for typelib in (UCRT64 / "lib" / "girepository-1.0").glob("*.typelib"):
        shutil.copy2(typelib, typelib_dir)

    _require(
        WEBVIEW2GTK_STAGE / "bin" / "libwebview2gtk-1-0.dll", "just init-webview2gtk"
    )
    for dll in (WEBVIEW2GTK_STAGE / "bin").glob("*.dll"):
        shutil.copy2(dll, STAGE)
    shutil.copy2(
        WEBVIEW2GTK_STAGE / "lib" / "girepository-1.0" / "WebView2Gtk-1.0.typelib",
        typelib_dir,
    )


def main() -> int:
    gresource = ROOT / "build" / "win" / "postcard.gresource"
    _require(gresource, "just build")

    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)

    shutil.copy2(gresource, STAGE / "postcard.gresource")
    shutil.copytree(
        UCRT64 / "share" / "icons" / "Adwaita", STAGE / "share" / "icons" / "Adwaita"
    )
    # tray.py looks this up itself via GLib.get_system_data_dirs()
    # (XDG_DATA_DIRS) -- without it the tray icon falls back to a plain
    # placeholder dot.
    shutil.copytree(
        ROOT / "data" / "icons" / "hicolor", STAGE / "share" / "icons" / "hicolor"
    )
    _stage_schemas()
    _stage_pixbuf_loaders()
    _stage_typelibs()

    icon = ROOT / "packaging" / "WinPostcard.ico"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onedir",
            "--noconfirm",
            "--windowed",
            "--name",
            "WinPostcard",
            "--distpath",
            str(DIST),
            "--workpath",
            str(WORK),
            "--paths",
            str(ROOT / "src"),
            "--add-data",
            f"{STAGE / 'postcard.gresource'};.",
            "--add-data",
            f"{STAGE / 'glib-2.0'};glib-2.0",
            "--add-data",
            f"{STAGE / 'share'};share",
            "--add-data",
            f"{STAGE / 'lib'};lib",
            "--add-binary",
            f"{STAGE}/*.dll;.",
            "--collect-all",
            "gi",
            *(["--icon", str(icon)] if icon.exists() else []),
            str(ROOT / "tools" / "win_app_entry.py"),
        ],
        check=True,
        cwd=ROOT,
    )
    print(f"win_package: built {DIST / 'WinPostcard' / 'WinPostcard.exe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
