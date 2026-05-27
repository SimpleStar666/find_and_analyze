from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QTextBrowser, QSplitter,
    QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ..models.repo import Repository
from ..services.github_service import GitHubService, GitHubServiceError
from ..services.ai_service import AIService, AIServiceError
from ..services.export_service import ExportService
from ..ui.settings_tab import load_config


class SearchWorker(QThread):
    result_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, github_service: GitHubService, query: str):
        super().__init__()
        self.github_service = github_service
        self.query = query

    def run(self):
        try:
            repos = self.github_service.search_repositories(self.query)
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
        search_bar.addWidget(self.search_input)

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
        layout.addLayout(search_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: none; border-radius: 4px; background-color: #ecf0f1; height: 6px; }
            QProgressBar::chunk { background-color: #3498db; border-radius: 4px; }
        """)
        layout.addWidget(self.progress_bar)

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
        self.summarize_btn = QPushButton("🤖 AI 总结")
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

        self.summarize_all_btn = QPushButton("🤖 批量总结所有")
        self.summarize_all_btn.setEnabled(False)
        self.summarize_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white;
                border: none; border-radius: 6px;
                padding: 8px 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
            QPushButton:pressed { background-color: #ba4a00; }
            QPushButton:disabled { background-color: #95a5a6; }
        """)
        self.summarize_all_btn.clicked.connect(self._do_summarize_all)
        action_bar.addWidget(self.summarize_all_btn)

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

        action_bar.addStretch()
        detail_layout.addLayout(action_bar)

        splitter.addWidget(detail_widget)
        splitter.setSizes([300, 500])
        layout.addWidget(splitter)

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

        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.repo_list.clear()
        self.detail_browser.clear()
        self.detail_header.setText("搜索中...")
        self.meta_label.setText("")
        self.repos = []

        self._search_worker = SearchWorker(self.github_service, query)
        self._search_worker.result_ready.connect(self._on_search_done)
        self._search_worker.error_occurred.connect(self._on_search_error)
        self._search_worker.start()

    def _on_search_done(self, repos):
        self.repos = repos
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.summarize_all_btn.setEnabled(len(repos) > 0)
        self.export_btn.setEnabled(len(repos) > 0)

        if not repos:
            self.detail_header.setText("未找到相关仓库，请尝试其他关键词")
            return

        self.detail_header.setText(f"找到 {len(repos)} 个仓库，点击查看详情")

        for repo in repos:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, repo)
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
            f"🔗 <a href='{repo.html_url}'>{repo.html_url}</a>",
        ]
        if repo.topics:
            meta_parts.append(f"🏷 {', '.join(repo.topics)}")
        self.meta_label.setText("  |  ".join(meta_parts))

        html = f"<p><b>简介：</b>{repo.description or '暂无描述'}</p>"
        if repo.ai_summary:
            html += f"<hr><h3>🤖 AI 总结</h3><div style='white-space: pre-wrap;'>{repo.ai_summary}</div>"
        else:
            html += "<p style='color: #95a5a6;'>点击「AI 总结」按钮生成智能总结</p>"
        self.detail_browser.setHtml(html)

        self._readme_worker = ReadmeWorker(self.github_service, repo.full_name)
        self._readme_worker.readme_ready.connect(self._on_readme_ready)
        self._readme_worker.start()

    def _on_readme_ready(self, full_name: str, readme: str):
        if self.current_repo and self.current_repo.full_name == full_name:
            self.current_repo.readme_content = readme
            if readme:
                escaped = readme.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                current_html = self.detail_browser.toHtml()
                readme_section = f"<hr><h3>📖 README</h3><pre style='white-space: pre-wrap; font-size: 12px; max-height: 300px; overflow-y: auto;'>{escaped[:5000]}</pre>"
                self.detail_browser.setHtml(current_html + readme_section)

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

    def _do_summarize_all(self):
        if not self.repos:
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

        self.summarize_all_btn.setEnabled(False)
        self.summarize_btn.setEnabled(False)
        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self._summarize_queue = [r for r in self.repos if not r.ai_summary]
        self._summarize_index = 0
        self._summarize_next()

    def _summarize_next(self):
        if self._summarize_index >= len(self._summarize_queue):
            self.summarize_all_btn.setEnabled(True)
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
