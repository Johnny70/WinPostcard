"""Entry point for the PyInstaller-packaged build (`just package`). Sets up
GI_TYPELIB_PATH/GSETTINGS_SCHEMA_DIR/XDG_DATA_DIRS relative to PyInstaller's
own bundle directory (sys._MEIPASS -- correct for both --onedir and
--onefile) before any gi import, then runs the same postcard.main entry
point as tools/win_run.py.
"""

import os
import sys
from pathlib import Path

if not getattr(sys, "frozen", False):
    raise RuntimeError("win_app_entry.py must be run from the PyInstaller-built exe")

_base = Path(sys._MEIPASS)  # noqa: SLF001 -- the documented, only way to find PyInstaller's bundle dir
os.add_dll_directory(str(_base))
# PyInstaller's own gi hooks (hook-gi.repository.Gtk.py etc.) hardcode
# GiModuleInfo('Gtk', '3.0') with no override for a GTK4 app -- they silently
# fail to find our actual Gtk-4.0/Gdk-4.0/etc. typelibs (confirmed: the DLLs
# still get bundled via the generic binary dependency walker, only the
# .typelib files are missing). win_package.py stages every needed typelib
# itself instead of trusting that hook -- this is the only place they can be
# found, so overwriting rather than extending GI_TYPELIB_PATH is correct.
os.environ["GI_TYPELIB_PATH"] = str(_base / "lib" / "girepository-1.0")
os.environ["GSETTINGS_SCHEMA_DIR"] = str(_base / "glib-2.0" / "schemas")
os.environ["XDG_DATA_DIRS"] = str(_base / "share")

from gi.repository import Gio  # noqa: E402

resource = Gio.Resource.load(str(_base / "postcard.gresource"))
resource._register()  # noqa: SLF001 -- GResource._register is the public entry point

from postcard.main import main as postcard_main  # noqa: E402

sys.exit(postcard_main("0.0.0-dev"))
