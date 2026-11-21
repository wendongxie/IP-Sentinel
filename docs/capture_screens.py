"""Capture the actual desktop widgets using an empty, disposable profile."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from ip_sentinel import notifications
from ip_sentinel.storage import History
from ip_sentinel.ui import Window, configure_app

out = Path(__file__).resolve().parent / "screenshots"
out.mkdir(exist_ok=True)
app = QApplication([])
configure_app(app)


def capture_dialog(name, show):
    def capture():
        dialog = app.activeModalWidget()
        assert dialog and dialog.grab().save(str(out / f"{name}.png"))
        dialog.reject()

    QTimer.singleShot(250, capture)
    show()


with TemporaryDirectory() as folder:
    database = History(Path(folder) / "screen.sqlite3")
    window = Window(database, start=False)
    window.show()
    app.processEvents()
    assert window.grab().save(str(out / "overview.png"))
    window.tabs.setCurrentIndex(1)
    app.processEvents()
    assert window.grab().save(str(out / "history.png"))
    with patch.object(notifications, "load", return_value=dict.fromkeys(notifications.FIELDS, "")):
        capture_dialog("settings", window.settings)
    capture_dialog("about", window.show_about)
    window.tray.hide()
    window.close()
    database.engine.dispose()
