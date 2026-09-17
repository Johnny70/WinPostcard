"""Launches WinPostcard from the `just build` output. The non-Flatpak
equivalent of postcard.in: same resource-loading, same entrypoint, run from
`just run` instead of an installed Flatpak tree.
"""

import sys

from gi.repository import Gio

RESOURCE_PATH = "build/win/postcard.gresource"


def main() -> int:
    resource = Gio.Resource.load(RESOURCE_PATH)
    resource._register()  # noqa: SLF001 -- GResource._register is the public entry point

    from postcard.main import main as postcard_main

    return postcard_main("0.0.0-dev")


if __name__ == "__main__":
    sys.exit(main())
