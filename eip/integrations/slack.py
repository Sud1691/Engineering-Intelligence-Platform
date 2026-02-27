from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import structlog

from eip.core.models import DeploymentEvent, RiskScore
from eip.core.secrets import get_secret
from eip.core.settings import get_settings


log = structlog.get_logger()


RISK_COLORS: Dict[str, str] = {
    "CRITICAL": "#E74C3C",
    "HIGH": "#E67E22",
    "MEDIUM": "#F1C40F",
    "LOW": "#2ECC71",
}


def _get_client() -> WebClient:
    settings = get_settings()
    secrets = get_secret(settings.integrations_secret_name)
    token = secrets.get("slack_bot_token")
    return WebClient(token=token)


def _build_blocks(event: DeploymentEvent, score: RiskScore) -> List[Dict[str, Any]]:
    header_text = f"Deployment risk for {event.service_name}: {score.tier} ({score.score}/100)"
    summary = score.explanation or score.recommended_action

    blocks: List[Dict[str, Any]] = [
        {"type": "header", "text": {"type": "plain_text", "text": header_text}},
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Service*: `{event.service_name}`  |  *Env*: `{event.environment}`  |  *Commit*: `{event.commit_sha[:8]}`",
                }
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": summary[:3000]},
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Build"},
                    "url": event.build_url,
                },
            ],
        },
    ]
    return blocks


async def notify_high_risk_deployment(
    event: DeploymentEvent,
    score: RiskScore,
    channel: str | None = None,
    dm_on_critical: bool = True,
) -> None:
    """
    Send a high/critical risk notification to Slack using Block Kit.
    """

    if score.tier not in {"HIGH", "CRITICAL"}:
        return

    if get_settings().runtime_mode == "stub":
        log.info(
            "slack_notification_stubbed",
            service=event.service_name,
            commit=event.commit_sha[:8],
            risk_tier=score.tier,
            channel=channel or "#deployments",
            dm_candidate=event.commit_author_email,
        )
        return

    client = _get_client()
    settings = get_settings()
    secrets = get_secret(settings.integrations_secret_name)
    default_channel = secrets.get("slack_default_channel", settings.slack_default_channel)
    target_channel = channel or default_channel

    attachments = [
        {
            "color": RISK_COLORS.get(score.tier, "#2ECC71"),
            "blocks": _build_blocks(event, score),
        }
    ]

    def _post_message() -> None:
        try:
            client.chat_postMessage(
                channel=target_channel,
                text=f"Deployment risk for {event.service_name}: {score.tier}",
                attachments=attachments,
            )
        except SlackApiError as exc:
            log.error(
                "slack_notification_failed",
                error=str(exc),
                service=event.service_name,
                commit=event.commit_sha[:8],
            )
            return

        if not dm_on_critical or score.tier != "CRITICAL" or not event.commit_author_email:
            return

        try:
            user = client.users_lookupByEmail(email=event.commit_author_email)
            user_id = user.get("user", {}).get("id")
            if not user_id:
                return

            client.chat_postMessage(
                channel=user_id,
                text=(
                    f"Critical deployment risk detected for {event.service_name} "
                    f"({score.score}/100). Please review before rollout."
                ),
                blocks=_build_blocks(event, score),
            )
        except SlackApiError as exc:
            log.warning(
                "slack_dm_notification_failed",
                error=str(exc),
                service=event.service_name,
                commit=event.commit_sha[:8],
                email=event.commit_author_email,
            )

    # Run the blocking Slack call in a thread to avoid blocking the event loop.
    await asyncio.to_thread(_post_message)
