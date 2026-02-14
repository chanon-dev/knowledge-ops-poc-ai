import httpx
from dataclasses import dataclass


@dataclass
class SlackConfig:
    bot_token: str
    default_channel: str | None = None


class SlackIntegration:
    def __init__(self, config: SlackConfig):
        self.config = config
        self.headers = {"Authorization": f"Bearer {config.bot_token}", "Content-Type": "application/json"}

    async def send_message(self, channel: str, text: str, blocks: list | None = None) -> dict:
        payload: dict = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def send_notification(self, text: str):
        channel = self.config.default_channel
        if not channel:
            return
        return await self.send_message(channel, text)

    async def send_approval_request(self, channel: str, question: str, answer: str, approval_url: str) -> dict:
        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*New answer requires approval*\n\n*Q:* {question}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*A:* {answer[:500]}"}},
            {"type": "actions", "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Review"}, "url": approval_url, "style": "primary"},
            ]},
        ]
        return await self.send_message(channel, f"Approval needed: {question}", blocks)
