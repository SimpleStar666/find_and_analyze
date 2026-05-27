from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Repository:
    name: str
    full_name: str
    html_url: str
    description: Optional[str]
    language: Optional[str]
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    topics: list = field(default_factory=list)
    readme_content: Optional[str] = None
    ai_summary: Optional[str] = None

    @property
    def display_name(self) -> str:
        return self.full_name

    @property
    def short_description(self) -> str:
        if not self.description:
            return "暂无描述"
        return self.description[:80] + "..." if len(self.description) > 80 else self.description
