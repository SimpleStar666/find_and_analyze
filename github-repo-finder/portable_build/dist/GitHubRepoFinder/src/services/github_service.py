import requests
from typing import List, Optional
from ..models.repo import Repository


class GitHubService:
    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"token {self.token}"
        self.session.headers["Accept"] = "application/vnd.github.v3+json"

    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc", per_page: int = 30) -> List[Repository]:
        url = f"{self.BASE_URL}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
        }
        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            repos = []
            for item in data.get("items", []):
                repo = Repository(
                    name=item.get("name", ""),
                    full_name=item.get("full_name", ""),
                    html_url=item.get("html_url", ""),
                    description=item.get("description"),
                    language=item.get("language"),
                    stargazers_count=item.get("stargazers_count", 0),
                    forks_count=item.get("forks_count", 0),
                    open_issues_count=item.get("open_issues_count", 0),
                    topics=item.get("topics", []),
                )
                repos.append(repo)
            return repos
        except requests.exceptions.RequestException as e:
            raise GitHubServiceError(f"搜索仓库失败: {str(e)}")

    def get_readme(self, full_name: str) -> Optional[str]:
        url = f"{self.BASE_URL}/repos/{full_name}/readme"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            import base64
            content = data.get("content", "")
            encoding = data.get("encoding", "base64")
            if encoding == "base64":
                return base64.b64decode(content).decode("utf-8", errors="replace")
            return content
        except requests.exceptions.RequestException:
            return None


class GitHubServiceError(Exception):
    pass
