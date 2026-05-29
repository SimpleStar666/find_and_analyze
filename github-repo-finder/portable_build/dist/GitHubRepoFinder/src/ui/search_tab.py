import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QTextBrowser, QSplitter,
    QMessageBox, QProgressBar, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ..models.repo import Repository
from ..services.github_service import GitHubService, GitHubServiceError
from ..services.ai_service import AIService, AIServiceError
from ..services.export_service import ExportService
from ..ui.settings_tab import load_config
from ..ui.favorites_tab import add_to_favorites
from ..ui.history_tab import add_search_record


SORT_OPTIONS = {
    "最佳匹配": "best-match",
    "最多 Star": "stars",
    "最多 Fork": "forks",
    "最近更新": "updated",
}

ORDER_OPTIONS = {
    "降序": "desc",
    "升序": "asc",
}


class SearchWorker(QThread):
    result_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, github_service: GitHubService, query: str, sort: str = "stars", order: str = "desc"):
        super().__init__()
        self.github_service = github_service
        self.query = query
        self.sort = sort
        self.order = order

    def run(self):
        try:
            repos = self.github_service.search_repositories(self.query, sort=self.sort, order=self.order)
            self.result_ready.emit(repos)
        except GitHubServiceError as e:
            self.error_occurred.emit(str(e))


class ReadmeWorker(QThread):
    readme_ready = pyqtSignal(str, str)

    def __init__(self, github_service: GitHubService, full_name: str):
        super().__init__()
        self.github_service = github_service
        self.full_name = full_name

    def run(self):
        readme = self.github_service.get_readme(self.full_name)
        self.readme_ready.emit(self.full_name, readme or "")


class SummarizeWorker(QThread):
    summary_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, ai_service: AIService, repo: Repository):
        super().__init__()
        self.ai_service = ai_service
        self.repo = repo

    def run(self):
        try:
            summary = self.ai_service.summarize_repo(self.repo)
            self.summary_ready.emit(summary)
        except AIServiceError as e:
            self.error_occurred.emit(str(e))


class SearchTab(QWidget):
    compare_requested = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repos = []
        self.current_repo = None
        self.github_service = GitHubService()
        self.ai_service = None
        self.export_service = ExportService()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        search_bar = QHBoxLayout()

        self.select_all_cb = QCheckBox("全选")
        self.select_all_cb.setStyleSheet("font-size: 12px; color: #2c3e50; padding: 0px 4px;")
        self.select_all_cb.stateChanged.connect(self._on_select_all_changed)

        self.selected_count_label = QLabel("0")
        self.selected_count_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 0px 2px;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索 GitHub 仓库（如：machine learning, web framework）...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 14px; font-size: 14px;
                border: 2px solid #bdc3c7; border-radius: 8px;
            }
            QLineEdit:focus { border-color: #3498db; }
        """)
        self.search_input.returnPressed.connect(self._do_search)
        search_bar.addWidget(self.search_input, stretch=3)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(SORT_OPTIONS.keys())
        self.sort_combo.setCurrentText("最多 Star")
        self.sort_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px; font-size: 13px;
                border: 2px solid #bdc3c7; border-radius: 6px;
                min-width: 100px;
            }
            QComboBox:hover { border-color: #3498db; }
            QComboBox::drop-down { border: none; }
        """)
        search_bar.addWidget(self.sort_combo)

        self.order_combo = QComboBox()
        self.order_combo.addItems(ORDER_OPTIONS.keys())
        self.order_combo.setCurrentText("降序")
        self.order_combo.setStyleSheet(self.sort_combo.styleSheet())
        search_bar.addWidget(self.order_combo)

        self.search_btn = QPushButton("🔍 搜索")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white;
                border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 14px; font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #2471a3; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.search_btn.clicked.connect(self._do_search)
        search_bar.addWidget(self.search_btn)
        search_bar.addWidget(self.select_all_cb)
        search_bar.addWidget(self.selected_count_label)
        layout.addLayout(search_bar, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; background-color: #ecf0f1; }
            QProgressBar::chunk { background-color: #3498db; border-radius: 4px; }
        """)
        layout.addWidget(self.progress_bar, 0)

        splitter = QSplitter(Qt.Horizontal)

        self.repo_list = QListWidget()
        self.repo_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7; border-radius: 6px;
                font-size: 13px; padding: 4px;
            }
            QListWidget::item {
                padding: 8px; border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db; color: white;
            }
            QListWidget::item:hover {
                background-color: #ebf5fb;
            }
        """)
        self.repo_list.currentItemChanged.connect(self._on_repo_selected)
        self.repo_list.itemChanged.connect(self._on_item_changed)
        splitter.addWidget(self.repo_list)

        detail_widget = QWidget()
        detail_layout = QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(8, 0, 0, 0)

        self.detail_header = QLabel("← 选择一个仓库查看详情")
        self.detail_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        self.detail_header.setWordWrap(True)
        detail_layout.addWidget(self.detail_header)

        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        self.meta_label.setWordWrap(True)
        detail_layout.addWidget(self.meta_label)

        self.copy_url_btn = QPushButton("📋 复制链接")
        self.copy_url_btn.setFixedHeight(28)
        self.copy_url_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1; color: #2c3e50;
                border: 1px solid #bdc3c7; border-radius: 4px;
                padding: 4px 10px; font-size: 12px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
        """)
        self.copy_url_btn.clicked.connect(self._copy_repo_url)
        self.copy_url_btn.setVisible(False)
        detail_layout.addWidget(self.copy_url_btn)

        self.detail_browser = QTextBrowser()
        self.detail_browser.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #bdc3c7; border-radius: 6px;
                padding: 8px; font-size: 13px;
                background-color: #fafafa;
            }
        """)
        self.detail_browser.setOpenExternalLinks(True)
        detail_layout.addWidget(self.detail_browser)

        action_bar = QHBoxLayout()
        self.summarize_btn = QPushButton("🤖 总结当前")
        self.summarize_btn.setEnabled(False)
        self.summarize_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6; color: white;
                border: none; border-radius: 6px;
                padding: 8px 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
            QPushButton:pressed { background-color: #7d3c98; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.summarize_btn.clicked.connect(self._do_summarize)
        action_bar.addWidget(self.summarize_btn)

        self.summarize_selected_btn = QPushButton("🤖 总结选中")
        self.summarize_selected_btn.setEnabled(False)
        self.summarize_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white;
                border: none; border-radius: 6px;
                padding: 8px 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
            QPushButton:pressed { background-color: #ba4a00; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.summarize_selected_btn.clicked.connect(self._do_summarize_selected)
        action_bar.addWidget(self.summarize_selected_btn)

        self.export_btn = QPushButton("📄 导出 Markdown")
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px;
                padding: 8px 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:pressed { background-color: #1e8449; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.export_btn.clicked.connect(self._do_export)
        action_bar.addWidget(self.export_btn)

        self.fav_btn = QPushButton("⭐ 收藏")
        self.fav_btn.setEnabled(False)
        self.fav_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12; color: white;
                border: none; border-radius: 6px;
                padding: 8px 14px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d68910; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.fav_btn.clicked.connect(self._do_favorite)
        action_bar.addWidget(self.fav_btn)

        self.compare_btn = QPushButton("📊 对比")
        self.compare_btn.setEnabled(False)
        self.compare_btn.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c; color: white;
                border: none; border-radius: 6px;
                padding: 8px 14px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #16a085; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.compare_btn.clicked.connect(self._do_compare)
        action_bar.addWidget(self.compare_btn)

        action_bar.addStretch()
        detail_layout.addLayout(action_bar)

        splitter.addWidget(detail_widget)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter, 1)

    def _get_selected_repos(self) -> list:
        selected = []
        for i in range(self.repo_list.count()):
            item = self.repo_list.item(i)
            if item.checkState() == Qt.Checked:
                repo = item.data(Qt.UserRole)
                if repo:
                    selected.append(repo)
        return selected

    def _update_selected_count(self):
        count = len(self._get_selected_repos())
        self.selected_count_label.setText(f"({count})")
        self.summarize_selected_btn.setEnabled(count > 0)

    def _on_select_all_changed(self, state):
        check_state = Qt.Checked if state == Qt.Checked else Qt.Unchecked
        self.repo_list.blockSignals(True)
        for i in range(self.repo_list.count()):
            self.repo_list.item(i).setCheckState(check_state)
        self.repo_list.blockSignals(False)
        self._update_selected_count()

    def _on_item_changed(self, item: QListWidgetItem):
        self._update_selected_count()
        checked_count = len(self._get_selected_repos())
        total_count = self.repo_list.count()
        self.select_all_cb.blockSignals(True)
        if checked_count == 0:
            self.select_all_cb.setCheckState(Qt.Unchecked)
        elif checked_count == total_count:
            self.select_all_cb.setCheckState(Qt.Checked)
        else:
            self.select_all_cb.setCheckState(Qt.PartiallyChecked)
        self.select_all_cb.blockSignals(False)

    def update_config(self, config: dict):
        self.github_service = GitHubService(token=config.get("github_token") or None)
        if config.get("api_key") and config.get("api_base") and config.get("model"):
            self.ai_service = AIService(
                api_base=config["api_base"],
                api_key=config["api_key"],
                model=config["model"],
            )

    def _do_search(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "提示", "请输入搜索关键词！")
            return

        config = load_config()
        self.github_service = GitHubService(token=config.get("github_token") or None)

        sort_key = SORT_OPTIONS[self.sort_combo.currentText()]
        order_key = ORDER_OPTIONS[self.order_combo.currentText()]

        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.repo_list.clear()
        self.detail_browser.clear()
        self.detail_header.setText("搜索中...")
        self.meta_label.setText("")
        self.repos = []
        self.select_all_cb.setChecked(False)

        self._search_worker = SearchWorker(self.github_service, query, sort=sort_key, order=order_key)
        self._search_worker.result_ready.connect(self._on_search_done)
        self._search_worker.error_occurred.connect(self._on_search_error)
        self._search_worker.start()

    def _on_search_done(self, repos):
        self.repos = repos
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.export_btn.setEnabled(len(repos) > 0)
        self.fav_btn.setEnabled(len(repos) > 0)
        self.compare_btn.setEnabled(len(repos) >= 2)

        if not repos:
            self.detail_header.setText("未找到相关仓库，请尝试其他关键词")
            return

        self.detail_header.setText(f"找到 {len(repos)} 个仓库，勾选后可批量总结")

        query = self.search_input.text().strip()
        sort_key = SORT_OPTIONS[self.sort_combo.currentText()]
        add_search_record(query, len(repos), sort=sort_key)

        for repo in repos:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, repo)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            stars = repo.stargazers_count
            lang = repo.language or "未知"
            item.setText(f"⭐ {stars:>6}  [{lang}]  {repo.full_name}")
            self.repo_list.addItem(item)

    def _on_search_error(self, error_msg):
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.detail_header.setText("搜索失败")
        QMessageBox.critical(self, "搜索错误", error_msg)

    def _on_repo_selected(self, current: QListWidgetItem, previous):
        if not current:
            self.summarize_btn.setEnabled(False)
            return
        repo = current.data(Qt.UserRole)
        self.current_repo = repo
        self.summarize_btn.setEnabled(True)

        self.detail_header.setText(f"📦 {repo.full_name}")
        meta_parts = [
            f"⭐ {repo.stargazers_count}",
            f"🍴 {repo.forks_count}",
            f"💻 {repo.language or '未知'}",
            f"🔗 {repo.html_url}",
        ]
        if repo.topics:
            meta_parts.append(f"🏷 {', '.join(repo.topics)}")
        self.meta_label.setText("  |  ".join(meta_parts))
        self.copy_url_btn.setVisible(True)

        html = f"<p><b>简介：</b>{repo.description or '暂无描述'}</p>"
        if repo.ai_summary:
            html += f"<hr><h3>🤖 AI 总结</h3><div style='white-space: pre-wrap;'>{repo.ai_summary}</div>"
        else:
            html += "<p style='color: #95a5a6;'>点击「总结当前」按钮生成智能总结</p>"
        self.detail_browser.setHtml(html)

        self._readme_worker = ReadmeWorker(self.github_service, repo.full_name)
        self._readme_worker.readme_ready.connect(self._on_readme_ready)
        self._readme_worker.start()

    def _on_readme_ready(self, full_name: str, readme: str):
        if self.current_repo and self.current_repo.full_name == full_name:
            self.current_repo.readme_content = readme
            if readme:
                readme_html = self._simple_markdown_to_html(readme[:8000])
                current_html = self.detail_browser.toHtml()
                readme_section = f"<hr><h3>📖 README</h3><div style='font-size: 14px; max-height: 400px; overflow-y: auto;'>{readme_html}</div>"
                self.detail_browser.setHtml(current_html + readme_section)

    def _simple_markdown_to_html(self, text: str) -> str:
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        text = re.sub(r'^### (.+)$', r'<h4>\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'`([^`]+)`', r'<code style="background:#f0f0f0;padding:2px 4px;border-radius:3px;">\1</code>', text)
        text = re.sub(r'^\[([^\]]+)\]\(([^)]+)\)$', r'<a href="\2">\1</a>', text, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        text = re.sub(r'^---$', '<hr>', text, flags=re.MULTILINE)
        text = re.sub(r'```(\w*)\n(.*?)```', r'<pre style="background:#2d2d2d;color:#f8f8f2;padding:12px;border-radius:6px;overflow-x:auto;font-size:13px;">\2</pre>', text, flags=re.DOTALL)
        text = re.sub(r'\n\n', '<br><br>', text)
        text = re.sub(r'\n', '<br>', text)
        return text

    def _copy_repo_url(self):
        if self.current_repo:
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(self.current_repo.html_url)
            self.copy_url_btn.setText("✅ 已复制")
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.copy_url_btn.setText("📋 复制链接"))

    def _do_summarize(self):
        if not self.current_repo:
            return
        config = load_config()
        if not config.get("api_key") or not config.get("api_base") or not config.get("model"):
            QMessageBox.warning(self, "提示", "请先在设置页面配置 AI 服务！")
            return
        self.ai_service = AIService(
            api_base=config["api_base"],
            api_key=config["api_key"],
            model=config["model"],
        )

        self.summarize_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.detail_header.setText("AI 正在总结...")

        self._summarize_worker = SummarizeWorker(self.ai_service, self.current_repo)
        self._summarize_worker.summary_ready.connect(self._on_summary_done)
        self._summarize_worker.error_occurred.connect(self._on_summary_error)
        self._summarize_worker.start()

    def _on_summary_done(self, summary: str):
        self.summarize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if self.current_repo:
            self.current_repo.ai_summary = summary
            self.detail_header.setText(f"📦 {self.current_repo.full_name}")
            html = self.detail_browser.toHtml()
            summary_html = f"<hr><h3>🤖 AI 总结</h3><div style='white-space: pre-wrap; background-color: #f0f9ff; padding: 12px; border-radius: 6px;'>{summary}</div>"
            self.detail_browser.setHtml(html + summary_html)

    def _on_summary_error(self, error_msg: str):
        self.summarize_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        if self.current_repo:
            self.detail_header.setText(f"📦 {self.current_repo.full_name}")
        QMessageBox.critical(self, "总结失败", error_msg)

    def _do_summarize_selected(self):
        selected = self._get_selected_repos()
        if not selected:
            QMessageBox.warning(self, "提示", "请先勾选要总结的仓库！")
            return
        config = load_config()
        if not config.get("api_key") or not config.get("api_base") or not config.get("model"):
            QMessageBox.warning(self, "提示", "请先在设置页面配置 AI 服务！")
            return
        self.ai_service = AIService(
            api_base=config["api_base"],
            api_key=config["api_key"],
            model=config["model"],
        )

        self.summarize_selected_btn.setEnabled(False)
        self.summarize_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self._summarize_queue = [r for r in selected if not r.ai_summary]
        if not self._summarize_queue:
            self.summarize_selected_btn.setEnabled(True)
            self.summarize_btn.setEnabled(True)
            self.search_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.detail_header.setText("选中的仓库已全部总结过")
            return
        self._summarize_index = 0
        self._summarize_next()

    def _summarize_next(self):
        if self._summarize_index >= len(self._summarize_queue):
            self.summarize_selected_btn.setEnabled(True)
            self.summarize_btn.setEnabled(True)
            self.search_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.detail_header.setText(f"批量总结完成！共总结 {len(self._summarize_queue)} 个仓库")
            return

        repo = self._summarize_queue[self._summarize_index]
        self.detail_header.setText(f"正在总结 ({self._summarize_index + 1}/{len(self._summarize_queue)}): {repo.full_name}")

        if not repo.readme_content:
            repo.readme_content = self.github_service.get_readme(repo.full_name) or ""

        self._batch_worker = SummarizeWorker(self.ai_service, repo)
        self._batch_worker.summary_ready.connect(self._on_batch_summary_done)
        self._batch_worker.error_occurred.connect(self._on_batch_summary_error)
        self._batch_worker.start()

    def _on_batch_summary_done(self, summary: str):
        if self._summarize_index < len(self._summarize_queue):
            self._summarize_queue[self._summarize_index].ai_summary = summary
        self._summarize_index += 1
        self._summarize_next()

    def _on_batch_summary_error(self, error_msg: str):
        self._summarize_index += 1
        self._summarize_next()

    def _do_export(self):
        if not self.repos:
            return
        keyword = self.search_input.text().strip()
        try:
            filepath = self.export_service.export_markdown(keyword, self.repos)
            QMessageBox.information(self, "导出成功", f"报告已导出到：\n{filepath}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _do_favorite(self):
        selected = self._get_selected_repos()
        if not selected:
            if self.current_repo:
                selected = [self.current_repo]
            else:
                QMessageBox.warning(self, "提示", "请先勾选或选择要收藏的仓库！")
                return
        added = 0
        for repo in selected:
            if add_to_favorites(repo):
                added += 1
        if added > 0:
            QMessageBox.information(self, "收藏成功", f"已收藏 {added} 个仓库到收藏夹！")
        else:
            QMessageBox.information(self, "提示", "这些仓库已在收藏夹中")

    def _do_compare(self):
        selected = self._get_selected_repos()
        if len(selected) < 2:
            QMessageBox.warning(self, "提示", "请至少勾选 2 个仓库进行对比！")
            return
        if len(selected) > 5:
            QMessageBox.warning(self, "提示", "最多同时对比 5 个仓库！")
            return
        if self.compare_requested:
            self.compare_requested(selected)
