"""Makes native DLLs discoverable when running pytest directly (an editor/IDE
run configuration, say) instead of through `just test`, which already sets
this up itself. A no-op on Linux, and a no-op on Windows too for whichever of
these isn't set/found.
"""

import os
import sys

if sys.platform == "win32":
    _ucrt64_bin = os.environ.get("UCRT64_DIR", r"C:\msys64\ucrt64\bin")
    if os.path.isdir(_ucrt64_bin):
        os.environ["PATH"] = _ucrt64_bin + os.pathsep + os.environ.get("PATH", "")

    # webview2-gtk (message_view.py / composer_window.py's WebKit replacement)
    # is a separate repo/build, not part of this one -- see docs/devlog.json
    # for why it stays out-of-tree. Default: a sibling checkout next to this
    # repo, same as WEBVIEW2GTK_DIR in justfile.
    _webview2gtk_dir = os.environ.get(
        "WEBVIEW2GTK_DIR", os.path.join(os.path.dirname(__file__), "..", "webview2-gtk")
    )
    _webview2gtk_stage = os.path.join(_webview2gtk_dir, "build", "install-staging")
    _webview2gtk_bin = os.path.join(_webview2gtk_stage, "bin")
    _webview2gtk_typelib = os.path.join(_webview2gtk_stage, "lib", "girepository-1.0")
    if os.path.isdir(_webview2gtk_bin):
        os.environ["PATH"] = _webview2gtk_bin + os.pathsep + os.environ.get("PATH", "")
    if os.path.isdir(_webview2gtk_typelib):
        os.environ["GI_TYPELIB_PATH"] = (
            _webview2gtk_typelib + os.pathsep + os.environ.get("GI_TYPELIB_PATH", "")
        )
