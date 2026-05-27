import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QGroupBox, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".github-repo-finder")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "api_base": "https://api.openai.com/v1",
    "api_key": "",
    "model": "gpt-3.5-turbo",
    "github_token": "",
}


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                for key, default in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = default
                return config
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


class SettingsTab(QWidget):
    config_saved = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("⚙ 设置")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)

        ai_group = QGroupBox("AI 服务配置")
        ai_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px; font-weight: bold;
                border: 1px solid #bdc3c7; border-radius: 6px;
                margin-top: 10px; padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 12px; padding: 0 6px;
            }
        """)
        ai_layout = QFormLayout()
        ai_layout.setSpacing(10)

        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("例如: https://api.openai.com/v1")
        ai_layout.addRow("API 地址:", self.api_base_input)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入你的 API Key")
        ai_layout.addRow("API Key:", self.api_key_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如: gpt-3.5-turbo, deepseek-chat")
        ai_layout.addRow("模型名称:", self.model_input)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        github_group = QGroupBox("GitHub 配置（可选）")
        github_group.setStyleSheet(ai_group.styleSheet())
        github_layout = QFormLayout()
        github_layout.setSpacing(10)

        self.github_token_input = QLineEdit()
        self.github_token_input.setEchoMode(QLineEdit.Password)
        self.github_token_input.setPlaceholderText("GitHub Personal Access Token（提高 API 限额）")
        github_layout.addRow("GitHub Token:", self.github_token_input)

        hint = QLabel("未配置 Token 时，GitHub API 限额为 10 次/分钟；配置后提升至 30 次/分钟")
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        hint.setWordWrap(True)
        github_layout.addRow(hint)

        github_group.setLayout(github_layout)
        layout.addWidget(github_group)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("💾 保存设置")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60; color: white;
                border: none; border-radius: 6px;
                padding: 10px 24px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #219a52; }
            QPushButton:pressed { background-color: #1e8449; }
        """)
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _load_settings(self):
        config = load_config()
        self.api_base_input.setText(config.get("api_base", ""))
        self.api_key_input.setText(config.get("api_key", ""))
        self.model_input.setText(config.get("model", ""))
        self.github_token_input.setText(config.get("github_token", ""))

    def _save_settings(self):
        config = {
            "api_base": self.api_base_input.text().strip(),
            "api_key": self.api_key_input.text().strip(),
            "model": self.model_input.text().strip(),
            "github_token": self.github_token_input.text().strip(),
        }
        if not config["api_base"] or not config["api_key"] or not config["model"]:
            QMessageBox.warning(self, "提示", "API 地址、API Key 和模型名称为必填项！")
            return
        save_config(config)
        self.config_saved.emit(config)
        QMessageBox.information(self, "成功", "设置已保存！")

    def get_current_config(self) -> dict:
        return load_config()
