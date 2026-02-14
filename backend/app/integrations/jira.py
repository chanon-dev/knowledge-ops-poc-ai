import httpx
from dataclasses import dataclass


@dataclass
class JiraConfig:
    base_url: str
    email: str
    api_token: str
    project_key: str


class JiraIntegration:
    def __init__(self, config: JiraConfig):
        self.config = config
        self.auth = (config.email, config.api_token)

    async def create_ticket(self, summary: str, description: str, issue_type: str = "Task") -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.config.base_url}/rest/api/3/issue",
                json={
                    "fields": {
                        "project": {"key": self.config.project_key},
                        "summary": summary,
                        "description": {"type": "doc", "version": 1, "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": description}]}
                        ]},
                        "issuetype": {"name": issue_type},
                    }
                },
                auth=self.auth,
            )
            resp.raise_for_status()
            return resp.json()

    async def add_comment(self, issue_key: str, comment: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.config.base_url}/rest/api/3/issue/{issue_key}/comment",
                json={"body": {"type": "doc", "version": 1, "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": comment}]}
                ]}},
                auth=self.auth,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_issue(self, issue_key: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.config.base_url}/rest/api/3/issue/{issue_key}",
                auth=self.auth,
            )
            resp.raise_for_status()
            return resp.json()
