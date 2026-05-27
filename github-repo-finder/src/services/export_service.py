import os
from datetime import datetime
from typing import List
from ..models.repo import Repository


class ExportService:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_markdown(self, keyword: str, repos: List[Repository]) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = f"github_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = os.path.join(self.output_dir, filename)

        lines = [
            f"# GitHub 仓库搜索报告",
            "",
            f"**搜索关键词**：{keyword}",
            f"**搜索时间**：{now}",
            f"**结果数量**：{len(repos)}",
            "",
            "---",
            "",
        ]

        for i, repo in enumerate(repos, 1):
            lines.append(f"## {i}. {repo.full_name} (⭐ {repo.stargazers_count})")
            lines.append("")
            lines.append(f"- **语言**：{repo.language or '未知'}")
            lines.append(f"- **地址**：{repo.html_url}")
            lines.append(f"- **Fork 数**：{repo.forks_count}")
            lines.append(f"- **简介**：{repo.description or '暂无描述'}")
            if repo.topics:
                lines.append(f"- **主题标签**：{', '.join(repo.topics)}")
            lines.append("")
            if repo.ai_summary:
                lines.append("### AI 总结")
                lines.append("")
                lines.append(repo.ai_summary)
                lines.append("")
            lines.append("---")
            lines.append("")

        content = "\n".join(lines)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
