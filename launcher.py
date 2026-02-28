"""Desktop launcher for the eDiscovery Toolkit.

Starts Streamlit in-process (no subprocess needed) and opens the
browser automatically. Works both as a normal Python script and inside
a frozen PyInstaller bundle.
"""

import os
import sys
import threading
import time
import webbrowser
from pathlib import Path

PORT = 8501
URL = f"http://localhost:{PORT}"


def _ensure_data_dir() -> Path:
    """Create ~/.ediscovery-toolkit/ for user data if it doesn't exist."""
    data_dir = Path.home() / ".ediscovery-toolkit"
    data_dir.mkdir(exist_ok=True)
    return data_dir


def _open_browser():
    """Open browser after a short delay to let Streamlit start."""
    time.sleep(3)
    webbrowser.open(URL)


def main():
    # Determine directories
    if getattr(sys, '_MEIPASS', None):
        # Running inside PyInstaller bundle
        app_dir = Path(sys._MEIPASS)
    else:
        # Running as normal script
        app_dir = Path(__file__).parent

    data_dir = _ensure_data_dir()

    # Tell config.py where to find/write user config
    os.environ['EDISCOVERY_DATA_DIR'] = str(data_dir)

    app_path = str(app_dir / "app.py")

    # Open browser in background thread (stcli.main() blocks)
    threading.Thread(target=_open_browser, daemon=True).start()

    # Start Streamlit in-process via its CLI entry point
    sys.argv = [
        "streamlit", "run", app_path,
        "--global.developmentMode=false",
        "--server.address=localhost",
        f"--server.port={PORT}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    from streamlit.web import cli as stcli
    stcli.main()


if __name__ == "__main__":
    main()
