from typing import Optional
from openai import OpenAI
from ..models.repo import Repository


SYSTEM_PROMPT = """你是一个专业的 GitHub 仓库分析助手。请根据用户提供的仓库信息，用中文生成一份简洁的总结报告。
报告必须包含以下部分：
1. 仓库用途：这个仓库是做什么的？
2. 核心功能：主要提供了哪些功能？
3. 适用场景：什么人/什么场景下会用到？
4. 技术栈：使用了哪些主要技术？
5. 推荐指数：⭐（1-5星）及推荐理由

请用清晰、专业的语言撰写，每部分2-3句话即可。"""


class AIService:
    def __init__(self, api_base: str, api_key: str, model: str):
        self.client = OpenAI(base_url=api_base, api_key=api_key)
        self.model = model

    def summarize_repo(self, repo: Repository) -> str:
        user_content = self._build_user_content(repo)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise AIServiceError(f"AI 总结失败: {str(e)}")

    def _build_user_content(self, repo: Repository) -> str:
        parts = [
            f"仓库名称：{repo.full_name}",
            f"仓库地址：{repo.html_url}",
            f"描述：{repo.description or '暂无描述'}",
            f"主要语言：{repo.language or '未知'}",
            f"星数：{repo.stargazers_count}",
            f"Fork 数：{repo.forks_count}",
            f"主题标签：{', '.join(repo.topics) if repo.topics else '无'}",
        ]
        if repo.readme_content:
            truncated = repo.readme_content[:3000]
            if len(repo.readme_content) > 3000:
                truncated += "\n\n... (README 内容过长，已截断)"
            parts.append(f"\nREADME 内容：\n{truncated}")
        return "\n".join(parts)


class AIServiceError(Exception):
    pass
