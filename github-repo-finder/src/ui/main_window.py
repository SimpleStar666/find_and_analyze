from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from .search_tab import SearchTab
from .settings_tab import SettingsTab, load_config


STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
}
QTabWidget::pane {
    border: 1px solid #bdc3c7; border-radius: 6px;
    padding: 4px; background-color: #ffffff;
}
QTabBar::tab {
    padding: 10px 24px; font-size: 14px; font-weight: bold;
    border: 1px solid #bdc3c7; border-bottom: none;
    border-top-left-radius: 8px; border-top-right-radius: 8px;
    background-color: #ecf0f1; color: #2c3e50;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background-color: #ffffff; color: #3498db;
    border-bottom: 2px solid #3498db;
}
QTabBar::tab:hover {
    background-color: #d5dbdb;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Repo Finder - 仓库搜索与智能总结")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 750)
        self.setStyleSheet(STYLESHEET)
        self._init_ui()
        self._apply_config()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 8, 12, 8)

        header = QLabel("🔍 GitHub Repo Finder")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #2c3e50; padding: 4px 0;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.search_tab = SearchTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.search_tab, "🔍 搜索")
        self.tabs.addTab(self.settings_tab, "⚙ 设置")

        layout.addWidget(self.tabs)

        self.settings_tab.config_saved.connect(self._on_config_saved)

    def _on_config_saved(self, config: dict):
        self.search_tab.update_config(config)

    def _apply_config(self):
        config = load_config()
        self.search_tab.update_config(config)
