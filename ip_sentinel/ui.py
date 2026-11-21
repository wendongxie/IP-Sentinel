"""IP Sentinel desktop shell."""
import json
import sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from time import monotonic, sleep

from PySide6.QtCore import QLibraryInfo, QLockFile, QObject, QStandardPaths, QTranslator, Signal
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QSystemTrayIcon, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from . import DISPLAY_VERSION, PRODUCT_TYPE, PUBLISHER, notifications
from .detection import TAGS, detect
from .monitor import Monitor
from .storage import History
from .risk_lists import RiskCache, evidence_line


def local_time(value):
    return datetime.fromisoformat(value).astimezone().strftime("%Y-%m-%d %H:%M:%S")


class Events(QObject):
    started = Signal()
    observed = Signal(object, object, str)
    finished = Signal(str)


class Window(QMainWindow):
    def __init__(self, history, start=True, risk=None):
        super().__init__()
        self.history = history
        self.page = 0
        self.exiting = False
        self.setWindowTitle("IP Sentinel · IP 哨兵")
        self.resize(880, 620)
        self.setMinimumSize(680, 470)
        icon = QApplication.instance().windowIcon()
        self.setWindowIcon(icon)
        self.statusBar().addPermanentWidget(QLabel(f"{PUBLISHER}出品"), 0)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.build_overview()
        self.build_history()
        self.tray = QSystemTrayIcon(icon, self)
        self.tray.setToolTip("IP Sentinel · IP 哨兵")
        menu = QMenu(self)
        menu.addAction("打开 IP Sentinel", self.restore)
        menu.addAction("立即检测", self.request_check)
        menu.addAction("退出", self.exit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()
        self.events = Events(self)
        self.events.started.connect(self.check_started)
        self.events.observed.connect(self.show_result)
        self.events.finished.connect(self.check_finished)
        self.monitor = Monitor(history, self.events.started.emit,
                               self.events.observed.emit, self.events.finished.emit, risk) if start else None
        if self.monitor:
            QApplication.instance().aboutToQuit.connect(self.monitor.shutdown)
        self.refresh_history()
        if self.monitor:
            self.request_check()

    def build_overview(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        title = QLabel("公网出口监控")
        title.setObjectName("heading")
        layout.addWidget(title)
        toolbar = QHBoxLayout()
        self.check = QPushButton("立即检测")
        self.check.clicked.connect(self.request_check)
        toolbar.addWidget(self.check)
        settings = QPushButton("凭据与通知设置")
        settings.clicked.connect(self.settings)
        toolbar.addWidget(settings)
        toolbar.addStretch()
        about = QPushButton("关于软件")
        about.clicked.connect(self.show_about)
        toolbar.addWidget(about)
        layout.addLayout(toolbar)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("等待首次检测…")
        layout.addWidget(self.details)
        note = QLabel("运行期间每小时检测。结果来自对应的探测端点，分流网络访问其他站点时可能使用不同出口。")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.tabs.addTab(tab, "当前出口")

    def show_about(self):
        QMessageBox.about(
            self,
            "关于 IP Sentinel",
            f"软件名称：IP Sentinel\n软件版本：{DISPLAY_VERSION}\n"
            f"产品类型：{PRODUCT_TYPE}\n开发出品：{PUBLISHER}",
        )

    def build_history(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("按 IP 或地址片段查询")
        self.search.returnPressed.connect(self.apply_filter)
        toolbar.addWidget(self.search, 1)
        for label, callback in (("查询", self.apply_filter), ("导出 CSV", self.export)):
            button = QPushButton(label)
            button.clicked.connect(callback)
            toolbar.addWidget(button)
        layout.addLayout(toolbar)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["本地时间", "协议", "出口 IP", "原 IP", "证据来源"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellDoubleClicked.connect(self.show_evidence)
        layout.addWidget(self.table)
        footer = QHBoxLayout()
        self.stats = QLabel()
        footer.addWidget(self.stats, 1)
        self.back = QPushButton("上一页")
        self.forward = QPushButton("下一页")
        self.back.clicked.connect(lambda: self.move_page(-1))
        self.forward.clicked.connect(lambda: self.move_page(1))
        footer.addWidget(self.back)
        footer.addWidget(self.forward)
        layout.addLayout(footer)
        self.tabs.addTab(tab, "历史与统计")
        self.filter = ""

    def request_check(self):
        if self.monitor and self.check.isEnabled():
            self.check_started()
            self.monitor.manual()

    def check_started(self):
        self.check.setEnabled(False)
        self.statusBar().showMessage("正在检测…")

    def check_finished(self, status):
        self.check.setEnabled(True)
        self.statusBar().showMessage(status)

    def show_result(self, timestamp, observations, message):
        lines = [f"检测时间  {local_time(timestamp.isoformat())}"]
        labels = {"country": "国家", "region": "地区", "city": "城市",
                  "asn": "ASN", "org": "AS 组织", "isp": "运营商"}
        for obs in observations:
            lines.extend(("", f"IPv{obs.family}   {obs.ip or '本次未观测到'}"))
            if obs.ip:
                lines.append(f"探测来源  {obs.source}")
                lines.extend(f"{label}  {obs.info.get(field, '未知')}"
                             for field, label in labels.items())
                lines.append(f"接口数据来源  {obs.metadata_source or '无'}")
                state = {None: "未知", True: "命中", False: "来源未标记"}
                lines.append("  ·  ".join(f"{tag.upper()} {state[obs.tags[tag]]}" for tag in TAGS))
                lines.extend(evidence_line(item) for item in obs.list_evidence)
                if obs.list_evidence:
                    lines.append("名单未收录仅表示该来源未找到记录。")
            lines.extend(obs.issues)
        self.details.setPlainText("\n".join(lines))
        self.refresh_history()
        if message and self.tray.isVisible():
            summary = "\n".join(f"IPv{obs.family}  {obs.previous} → {obs.ip}"
                                for obs in observations if obs.previous)
            self.tray.showMessage("IP Sentinel · 出口 IP 已变化", summary)

    def apply_filter(self):
        self.filter = self.search.text().strip()
        self.page = 0
        self.refresh_history()

    def move_page(self, delta):
        self.page += delta
        self.refresh_history()

    def refresh_history(self):
        self.rows, (total, changes, unique) = self.history.query(self.filter, self.page)
        self.table.setRowCount(len(self.rows))
        for index, row in enumerate(self.rows):
            columns = (local_time(row["observed_at"]), f"IPv{row['family']}",
                       row["ip"] or "未观测到", row["previous"],
                       row["evidence"]["metadata_source"])
            for column, value in enumerate(columns):
                self.table.setItem(index, column, QTableWidgetItem(value))
        self.table.resizeColumnsToContents()
        self.stats.setText(f"记录 {total}  ·  变化 {changes}  ·  不同 IP {unique}  ·  第 {self.page + 1} 页")
        self.back.setEnabled(self.page > 0)
        self.forward.setEnabled((self.page + 1) * 100 < total)

    def show_evidence(self, row, _column):
        dialog = QDialog(self)
        dialog.setWindowTitle("历史检测证据")
        dialog.resize(660, 460)
        layout = QVBoxLayout(dialog)
        evidence = QPlainTextEdit(json.dumps(self.rows[row]["evidence"], ensure_ascii=False, indent=2))
        evidence.setReadOnly(True)
        layout.addWidget(evidence)
        dialog.exec()

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出当前查询", "ip-sentinel.csv", "CSV (*.csv)")
        if path:
            try:
                self.history.export(path, self.filter)
                self.statusBar().showMessage("CSV 已导出")
            except OSError as exc:
                QMessageBox.warning(self, "导出失败", str(exc))

    def settings(self):
        try:
            values = notifications.load()
        except Exception as exc:
            QMessageBox.warning(self, "凭据读取失败", type(exc).__name__)
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("凭据与通知设置")
        layout = QFormLayout(dialog)
        info = QLabel("凭据保存在 Windows 凭据管理器。留空并保存可清除对应配置。")
        layout.addRow(info)
        inputs = {}
        for name, label in notifications.FIELDS.items():
            entry = QLineEdit(values[name])
            entry.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addRow(label, entry)
            inputs[name] = entry
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        while dialog.exec():
            try:
                notifications.save({name: entry.text().strip() for name, entry in inputs.items()})
                self.statusBar().showMessage("设置已保存")
                break
            except ValueError as exc:
                QMessageBox.warning(dialog, "检查设置", str(exc))
            except Exception as exc:
                QMessageBox.warning(dialog, "凭据保存失败", type(exc).__name__)

    def tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self.restore()

    def restore(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def exit(self):
        self.exiting = True
        QApplication.instance().quit()

    def closeEvent(self, event):
        if self.tray.isVisible() and not self.exiting:
            event.ignore()
            self.hide()
        else:
            event.accept()


def activate_running_instance(server_name, lock):
    deadline = monotonic() + 1.5
    while monotonic() < deadline:
        socket = QLocalSocket()
        socket.connectToServer(server_name)
        if socket.waitForConnected(100):
            socket.disconnectFromServer()
            return True
        if lock.tryLock(0):
            return False
        sleep(0.05)
    raise RuntimeError("现有实例未响应。请从系统托盘打开或退出后重试。")


def activation_server(server_name, window):
    server = QLocalServer(window)
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    if not server.listen(server_name):
        raise RuntimeError("无法建立本地窗口唤醒通道。")

    def restore_window():
        while server.hasPendingConnections():
            socket = server.nextPendingConnection()
            socket.disconnectFromServer()
            socket.deleteLater()
        window.restore()

    server.newConnection.connect(restore_window)
    return server


def configure_app(app):
    translator = QTranslator(app)
    translations = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if translator.load("qtbase_zh_CN", translations):
        app.installTranslator(translator)
    app.setOrganizationName("IP Sentinel")
    app.setApplicationName("IP Sentinel")
    app.setApplicationVersion(DISPLAY_VERSION)
    assets = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "assets"
    app.setWindowIcon(QIcon(str(assets / "icons" / "ip-sentinel.ico")))
    app.setStyleSheet("""
        QMainWindow, QDialog { background: #f0f4f9; }
        QLabel#heading { font-size: 27px; font-weight: 700; color: #132d48; padding: 8px; }
        QPushButton { background: #e1edfa; border: 1px solid #b0c8df;
                      padding: 6px 13px; border-radius: 5px; color: #132d48; }
        QPushButton:disabled { color: #596676; background: #e8edf2; }
        QPlainTextEdit, QTableWidget, QLineEdit { background: white; color: #132d48;
                                                border: 1px solid #b0c8df; padding: 4px; }
    """)


def main():
    app = QApplication(sys.argv)
    configure_app(app)
    if "--live-smoke-test" in sys.argv:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            db = History(Path(directory) / "live.sqlite3")
            try:
                timestamp, observations = detect()
                db.record(timestamp, observations)
                rows, _stats = db.query()
                return 0 if len(rows) == 2 and any(row["ip"] for row in rows) else 2
            finally:
                db.engine.dispose()
    smoke = "--smoke-test" in sys.argv
    if smoke:
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as path:
            database = History(Path(path) / "history.sqlite3")
            window = Window(database, start=False)
            window.show()
            app.processEvents()
            assert window.isVisible() and window.tabs.count() == 2
            assert not window.windowIcon().isNull() and not window.tray.icon().isNull()
            assert any(label.text() == f"{PUBLISHER}出品"
                       for label in window.statusBar().findChildren(QLabel))
            name = "IPSentinel-smoke-" + sha256(path.encode()).hexdigest()
            server = activation_server(name, window)
            lock = QLockFile(str(Path(path) / "smoke.lock"))
            assert lock.tryLock(0)
            window.hide()
            assert activate_running_instance(name, lock)
            deadline = monotonic() + 2
            while not window.isVisible() and monotonic() < deadline:
                app.processEvents()
                sleep(0.01)
            assert window.isVisible(), "Activation did not restore the window"
            server.close()
            lock.unlock()
            window.tray.hide()
            window.close()
            database.engine.dispose()
        return 0
    try:
        path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.GenericDataLocation)) / "IP Sentinel"
        path.mkdir(parents=True, exist_ok=True)
        lock = QLockFile(str(path / "running.lock"))
        lock.setStaleLockTime(0)
        name = "IPSentinel-" + sha256(str(path.resolve()).casefold().encode()).hexdigest()
        if not lock.tryLock(0) and activate_running_instance(name, lock):
            return 0
        window = Window(History(path / "history.sqlite3"), risk=RiskCache(path / "risk-lists"))
        server = activation_server(name, window)
    except Exception as exc:
        detail = str(exc) if type(exc) is RuntimeError else type(exc).__name__
        QMessageBox.critical(None, "IP Sentinel 启动失败", detail)
        return 1
    window.show()
    result = app.exec()
    server.close()
    lock.unlock()
    return result








