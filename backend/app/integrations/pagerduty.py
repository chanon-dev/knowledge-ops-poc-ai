import httpx
from dataclasses import dataclass


@dataclass
class PagerDutyConfig:
    api_key: str
    service_id: str
    from_email: str


class PagerDutyIntegration:
    BASE_URL = "https://api.pagerduty.com"

    def __init__(self, config: PagerDutyConfig):
        self.config = config
        self.headers = {
            "Authorization": f"Token token={config.api_key}",
            "Content-Type": "application/json",
            "From": config.from_email,
        }

    async def create_incident(self, title: str, body: str, urgency: str = "high") -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/incidents",
                json={
                    "incident": {
                        "type": "incident",
                        "title": title,
                        "service": {"id": self.config.service_id, "type": "service_reference"},
                        "urgency": urgency,
                        "body": {"type": "incident_body", "details": body},
                    }
                },
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def resolve_incident(self, incident_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.BASE_URL}/incidents/{incident_id}",
                json={"incident": {"type": "incident_reference", "status": "resolved"}},
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()
