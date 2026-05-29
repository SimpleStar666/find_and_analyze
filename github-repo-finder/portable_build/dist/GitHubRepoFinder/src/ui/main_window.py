import os
import sys
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from .search_tab import SearchTab
from .trending_tab import TrendingTab
from .compare_tab import CompareTab
from .favorites_tab import FavoritesTab
from .history_tab import HistoryTab
from .settings_tab import SettingsTab, load_config


STYLESHEET = """
QMainWindow {
    background-color: #ffffff;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #bdc3c7; border-radius: 6px;
    padding: 4px; background-color: #ffffff;
}
QTabBar::tab {
    padding: 10px 20px; font-size: 15px; font-weight: bold;
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
        self._set_icon()
        self._init_ui()
        self._apply_config()

    def _set_icon(self):
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base, "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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
        self.trending_tab = TrendingTab()
        self.compare_tab = CompareTab()
        self.favorites_tab = FavoritesTab()
        self.history_tab = HistoryTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.search_tab, "🔍 搜索")
        self.tabs.addTab(self.trending_tab, "🔥 趋势")
        self.tabs.addTab(self.compare_tab, "📊 对比")
        self.tabs.addTab(self.favorites_tab, "⭐ 收藏")
        self.tabs.addTab(self.history_tab, "📜 历史")
        self.tabs.addTab(self.settings_tab, "⚙ 设置")

        layout.addWidget(self.tabs)

        self.settings_tab.config_saved.connect(self._on_config_saved)
        self.search_tab.compare_requested.connect(self._on_compare_requested)
        self.trending_tab.compare_requested.connect(self._on_compare_requested)
        self.history_tab.search_requested = self._on_history_search
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _on_config_saved(self, config: dict):
        self.search_tab.update_config(config)
        self.trending_tab.update_config(config)

    def _apply_config(self):
        config = load_config()
        self.search_tab.update_config(config)
        self.trending_tab.update_config(config)

    def _on_compare_requested(self, repos):
        self.compare_tab.add_repos(list(repos))
        self.tabs.setCurrentWidget(self.compare_tab)

    def _on_history_search(self, query: str, sort: str):
        self.search_tab.search_input.setText(query)
        sort_map = {v: k for k, v in {
            "最佳匹配": "best-match",
            "最多 Star": "stars",
            "最多 Fork": "forks",
            "最近更新": "updated",
        }.items()}
        if sort in sort_map:
            self.search_tab.sort_combo.setCurrentText(sort_map[sort])
        self.tabs.setCurrentWidget(self.search_tab)
        self.search_tab._do_search()

    def _on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget == self.favorites_tab:
            self.favorites_tab.refresh()
        elif widget == self.history_tab:
            self.history_tab.refresh()
