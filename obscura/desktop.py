import sys
import threading
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QStyle
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import __version__
from .autostart import is_enabled as autostart_is_enabled
from .autostart import set_enabled as set_autostart
from .config import AppConfig, CustomRule, load_config, save_config
from .monitor import ClipboardMonitor, DirectoryMonitor
from .updater import check_for_update, download_update, install_update


TEXT = {
    "fr": {
        "settings": "Paramètres Obscura",
        "general": "Général",
        "monitoring": "Surveillance",
        "detection": "Détection",
        "redaction": "Masquage",
        "output": "Sorties",
        "notifications": "Notifications",
        "about": "À propos",
        "save": "Enregistrer",
        "clipboard": "Surveiller le presse-papiers",
        "folder": "Surveiller un dossier",
        "autostart": "Lancer au démarrage",
        "quit": "Quitter",
        "update": "Mettre à jour vers {version}",
    },
    "en": {
        "settings": "Obscura settings",
        "general": "General",
        "monitoring": "Monitoring",
        "detection": "Detection",
        "redaction": "Redaction",
        "output": "Outputs",
        "notifications": "Notifications",
        "about": "About",
        "save": "Save",
        "clipboard": "Watch clipboard",
        "folder": "Watch a folder",
        "autostart": "Launch at startup",
        "quit": "Quit",
        "update": "Update to {version}",
    },
}

CATEGORY_LABELS = {
    "email": "E-mail", "ipv4": "IP address", "phone": "Phone number", "credit_card": "Credit card",
    "credential": "Password / secret", "api_key": "API key", "jwt": "Token", "github_token": "GitHub token",
    "aws_key": "AWS key", "base64_key": "Key-like value", "iban": "IBAN", "mac": "MAC address",
    "endpoint": "Endpoint", "ssn_fr": "French social security", "private_key": "Private key",
}


class UiBridge(QObject):
    redaction_completed = Signal(object)
    error_occurred = Signal(object)
    update_available = Signal(object)


class SettingsWindow(QDialog):
    def __init__(self, app: "ObscuraApplication"):
        super().__init__()
        self.app = app
        self.config = app.config
        self.setWindowTitle(self.t("settings"))
        self.resize(600, 560)
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._general_tab()
        self._monitoring_tab()
        self._detection_tab()
        self._redaction_tab()
        self._output_tab()
        self._notifications_tab()
        self._about_tab()
        buttons = QHBoxLayout()
        buttons.addStretch()
        save = QPushButton(self.t("save"))
        save.clicked.connect(self.save)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def t(self, key: str) -> str:
        return TEXT[self.config.language][key]

    def _tab(self, name: str) -> tuple[QWidget, QFormLayout]:
        widget = QWidget()
        layout = QFormLayout(widget)
        self.tabs.addTab(widget, name)
        return widget, layout

    def _general_tab(self) -> None:
        _, layout = self._tab(self.t("general"))
        self.language = QComboBox()
        self.language.addItem("Français", "fr")
        self.language.addItem("English", "en")
        self.language.setCurrentIndex(0 if self.config.language == "fr" else 1)
        self.autostart = QCheckBox(self.t("autostart"))
        self.autostart.setChecked(autostart_is_enabled())
        reset = QPushButton("Restore defaults" if self.config.language == "en" else "Restaurer les valeurs par défaut")
        reset.clicked.connect(self.reset_defaults)
        layout.addRow("Language", self.language)
        layout.addRow(self.autostart)
        layout.addRow(reset)

    def _monitoring_tab(self) -> None:
        _, layout = self._tab(self.t("monitoring"))
        self.clipboard = QCheckBox(self.t("clipboard"))
        self.clipboard.setChecked(self.config.clipboard_enabled)
        self.interval = QSpinBox()
        self.interval.setRange(100, 10000)
        self.interval.setSuffix(" ms")
        self.interval.setValue(int(self.config.clipboard_interval * 1000))
        self.folder = QCheckBox(self.t("folder"))
        self.folder.setChecked(self.config.watch_directory_enabled)
        self.watch_path = QLineEdit(self.config.watch_directory)
        select = QPushButton("Browse…")
        select.clicked.connect(lambda: self.select_directory(self.watch_path))
        watch_row = QHBoxLayout()
        watch_row.addWidget(self.watch_path)
        watch_row.addWidget(select)
        self.recursive = QCheckBox("Recursive")
        self.recursive.setChecked(self.config.recursive_watch)
        layout.addRow(self.clipboard)
        layout.addRow("Interval", self.interval)
        layout.addRow(self.folder)
        layout.addRow("Folder", watch_row)
        layout.addRow(self.recursive)

    def _detection_tab(self) -> None:
        widget, layout = self._tab(self.t("detection"))
        self.ocr_languages = QLineEdit(", ".join(self.config.ocr_languages))
        self.confidence = QSpinBox()
        self.confidence.setRange(0, 100)
        self.confidence.setValue(self.config.ocr_confidence)
        layout.addRow("OCR languages", self.ocr_languages)
        layout.addRow("OCR confidence", self.confidence)
        categories = QGroupBox("Categories")
        categories_layout = QVBoxLayout(categories)
        self.category_checks: dict[str, QCheckBox] = {}
        for category, label in CATEGORY_LABELS.items():
            checkbox = QCheckBox(label)
            checkbox.setChecked(category in self.config.active_categories)
            self.category_checks[category] = checkbox
            categories_layout.addWidget(checkbox)
        self.custom_rules = QLineEdit("; ".join(rule.value for rule in self.config.custom_rules if rule.enabled))
        self.faces = QCheckBox("Local face detection (optional model)")
        self.faces.setChecked(self.config.face_detection_enabled)
        self.names = QCheckBox("Local name detection (optional model)")
        self.names.setChecked(self.config.name_detection_enabled)
        layout.addRow(categories)
        layout.addRow("Custom keywords", self.custom_rules)
        layout.addRow(self.faces)
        layout.addRow(self.names)

    def _redaction_tab(self) -> None:
        _, layout = self._tab(self.t("redaction"))
        self.mode = QComboBox()
        self.mode.addItem("Black", "black")
        self.mode.addItem("Blur", "blur")
        self.mode.addItem("Pixelate", "pixelate")
        self.mode.setCurrentIndex(["black", "blur", "pixelate"].index(self.config.redaction_mode))
        self.blur = QSpinBox()
        self.blur.setRange(1, 100)
        self.blur.setValue(self.config.blur_radius)
        self.pixel = QSpinBox()
        self.pixel.setRange(2, 100)
        self.pixel.setValue(self.config.pixel_size)
        layout.addRow("Style", self.mode)
        layout.addRow("Blur radius", self.blur)
        layout.addRow("Pixel size", self.pixel)

    def _output_tab(self) -> None:
        _, layout = self._tab(self.t("output"))
        self.output_path = QLineEdit(self.config.output_directory)
        select = QPushButton("Browse…")
        select.clicked.connect(lambda: self.select_directory(self.output_path))
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_path)
        output_row.addWidget(select)
        self.suffix = QLineEdit(self.config.output_suffix)
        self.replace = QCheckBox("Replace source files")
        self.replace.setChecked(self.config.replace_source)
        self.copy_outputs = QCheckBox("Copy file results to clipboard")
        self.copy_outputs.setChecked(self.config.copy_file_output_to_clipboard)
        layout.addRow("Output folder", output_row)
        layout.addRow("Suffix", self.suffix)
        layout.addRow(self.replace)
        layout.addRow(self.copy_outputs)

    def _notifications_tab(self) -> None:
        _, layout = self._tab(self.t("notifications"))
        self.notifications = QCheckBox("Notify when a redaction is applied")
        self.notifications.setChecked(self.config.notifications_enabled)
        self.critical_notifications = QCheckBox("Notify about critical security updates")
        self.critical_notifications.setChecked(self.config.critical_update_notifications)
        layout.addRow(self.notifications)
        layout.addRow(self.critical_notifications)

    def _about_tab(self) -> None:
        _, layout = self._tab(self.t("about"))
        layout.addRow(QLabel(f"Obscura {__version__}"))
        layout.addRow(QLabel("Offline screenshot redaction. Images and OCR data stay on this device."))
        check = QPushButton("Check for updates")
        check.clicked.connect(self.app.check_updates)
        layout.addRow(check)

    def select_directory(self, field: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select folder", field.text() or str(Path.home()))
        if path:
            field.setText(path)

    def reset_defaults(self) -> None:
        self.app.config = AppConfig()
        self.reject()
        self.app.open_settings()

    def save(self) -> None:
        if self.replace.isChecked() and QMessageBox.question(self, "Confirm", "Source files will be overwritten. Continue?") != QMessageBox.Yes:
            return
        config = self.app.config
        config.language = self.language.currentData()
        config.autostart_enabled = self.autostart.isChecked()
        config.clipboard_enabled = self.clipboard.isChecked()
        config.clipboard_interval = self.interval.value() / 1000
        config.watch_directory_enabled = self.folder.isChecked()
        config.watch_directory = self.watch_path.text().strip()
        config.recursive_watch = self.recursive.isChecked()
        config.ocr_languages = [value.strip() for value in self.ocr_languages.text().split(",")]
        config.ocr_confidence = self.confidence.value()
        config.active_categories = {name for name, checkbox in self.category_checks.items() if checkbox.isChecked()}
        config.custom_rules = [CustomRule(name=value.strip(), value=value.strip()) for value in self.custom_rules.text().split(";") if value.strip()]
        config.face_detection_enabled = self.faces.isChecked()
        config.name_detection_enabled = self.names.isChecked()
        config.redaction_mode = self.mode.currentData()
        config.blur_radius = self.blur.value()
        config.pixel_size = self.pixel.value()
        config.output_directory = self.output_path.text().strip()
        config.output_suffix = self.suffix.text().strip()
        config.replace_source = self.replace.isChecked()
        config.copy_file_output_to_clipboard = self.copy_outputs.isChecked()
        config.notifications_enabled = self.notifications.isChecked()
        config.critical_update_notifications = self.critical_notifications.isChecked()
        config.normalize()
        set_autostart(config.autostart_enabled)
        save_config(config)
        self.app.reconfigure()
        self.accept()


class ObscuraApplication(QObject):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.qt = QApplication(sys.argv)
        self.qt.setQuitOnLastWindowClosed(False)
        icon_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1])) / "obscura.svg"
        icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon.fromTheme("security-high")
        self.tray = QSystemTrayIcon(icon, self.qt)
        if self.tray.icon().isNull():
            self.tray.setIcon(self.qt.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self._ui_bridge = UiBridge(self)
        self._ui_bridge.redaction_completed.connect(self._notify_result, Qt.ConnectionType.QueuedConnection)
        self._ui_bridge.error_occurred.connect(self._notify_error, Qt.ConnectionType.QueuedConnection)
        self._ui_bridge.update_available.connect(self._set_update, Qt.ConnectionType.QueuedConnection)
        self.clipboard_monitor: Optional[ClipboardMonitor] = None
        self.directory_monitor: Optional[DirectoryMonitor] = None
        self.update = None
        self.menu = QMenu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._activate)
        self.reconfigure()
        self.tray.show()

    def _activate(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings()

    @Slot(object)
    def _notify_result(self, result) -> None:
        if self.config.notifications_enabled:
            self.tray.showMessage("Obscura", f"Redacted {result.count} sensitive region(s).")

    @Slot(object)
    def _notify_error(self, error: Exception) -> None:
        self.tray.showMessage("Obscura", str(error), QSystemTrayIcon.MessageIcon.Warning)

    def reconfigure(self) -> None:
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
        if self.directory_monitor:
            self.directory_monitor.stop()
        if self.config.clipboard_enabled:
            self.clipboard_monitor = ClipboardMonitor(
                self.config,
                self._ui_bridge.redaction_completed.emit,
                self._ui_bridge.error_occurred.emit,
            )
            self.clipboard_monitor.start()
        else:
            self.clipboard_monitor = None
        if self.config.watch_directory_enabled and self.config.watch_directory:
            self.directory_monitor = DirectoryMonitor(
                self.config,
                self._ui_bridge.redaction_completed.emit,
                self._ui_bridge.error_occurred.emit,
            )
            self.directory_monitor.start()
        else:
            self.directory_monitor = None
        self.rebuild_menu()

    def rebuild_menu(self) -> None:
        self.menu.clear()
        if self.update:
            action = self.menu.addAction(TEXT[self.config.language]["update"].format(version=self.update.version))
            action.triggered.connect(self.install_available_update)
            self.menu.addSeparator()
        clipboard = QAction(TEXT[self.config.language]["clipboard"], self.menu, checkable=True)
        clipboard.setChecked(self.config.clipboard_enabled)
        clipboard.toggled.connect(self.toggle_clipboard)
        self.menu.addAction(clipboard)
        folder = QAction(TEXT[self.config.language]["folder"], self.menu, checkable=True)
        folder.setChecked(self.config.watch_directory_enabled)
        folder.toggled.connect(self.toggle_directory)
        self.menu.addAction(folder)
        autostart = QAction(TEXT[self.config.language]["autostart"], self.menu, checkable=True)
        autostart.setChecked(autostart_is_enabled())
        autostart.toggled.connect(self.toggle_autostart)
        self.menu.addAction(autostart)
        self.menu.addSeparator()
        self.menu.addAction(TEXT[self.config.language]["settings"], self.open_settings)
        self.menu.addAction(TEXT[self.config.language]["about"], self.open_about)
        self.menu.addSeparator()
        self.menu.addAction(TEXT[self.config.language]["quit"], self.quit)

    def toggle_clipboard(self, value: bool) -> None:
        self.config.clipboard_enabled = value
        save_config(self.config)
        self.reconfigure()

    def toggle_directory(self, value: bool) -> None:
        self.config.watch_directory_enabled = value
        save_config(self.config)
        self.reconfigure()

    def toggle_autostart(self, value: bool) -> None:
        self.config.autostart_enabled = value
        set_autostart(value)
        save_config(self.config)

    def open_settings(self) -> None:
        SettingsWindow(self).exec()

    def open_about(self) -> None:
        QMessageBox.information(None, "About Obscura", f"Obscura {__version__}\n\nOffline screenshot redaction.")

    @Slot(object)
    def _set_update(self, update) -> None:
        self.update = update
        self.rebuild_menu()
        if update.critical and self.config.critical_update_notifications:
            self.tray.showMessage("Obscura", f"Critical update {update.version} available.", QSystemTrayIcon.MessageIcon.Warning)

    def check_updates_silently(self, force: bool = False) -> None:
        def worker() -> None:
            try:
                update = check_for_update(
                    interval_hours=self.config.update_check_interval_hours,
                    force=force,
                )
            except Exception:
                return
            if update:
                self._ui_bridge.update_available.emit(update)
        threading.Thread(target=worker, daemon=True).start()

    def check_updates(self) -> None:
        self.tray.showMessage("Obscura", "Checking for updates…")
        self.check_updates_silently(force=True)

    def install_available_update(self) -> None:
        if not self.update:
            return
        try:
            downloaded = download_update(self.update)
            install_update(downloaded)
            self.quit()
        except Exception as exc:
            QMessageBox.warning(None, "Obscura", str(exc))

    def quit(self) -> None:
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
        if self.directory_monitor:
            self.directory_monitor.stop()
        self.tray.hide()
        self.qt.quit()

    def run(self) -> int:
        return self.qt.exec()


def main() -> None:
    raise SystemExit(ObscuraApplication().run())
