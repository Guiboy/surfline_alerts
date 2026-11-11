"""Workflow d'alertes surf Open-Meteo (Martigues → Hyères)."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pydantic
import mistralai.workflows as workflows
from mistralai.workflows import Depends
from mistralai.workflows.plugins.mistralai.connectors import (
    ToolCallClient,
    connector,
    uses_connectors,
)

from worker.config import DEFAULT_RECIPIENT, SPOTS
from worker.mailer import send_email_smtp
from worker.selection import build_email

gmail_connector = connector(
    "gmail", run_as="deployment", auto_auth=False, credentials_name="ramilopfamily-gmail-com"
)


class SurfAlertInput(pydantic.BaseModel):
    recipient_email: str = DEFAULT_RECIPIENT
    min_rating: str = "FAIR_TO_GOOD"
    days_ahead: list[int] = [1, 2, 3, 4, 5, 6, 7]
    day_start_hour: int = 6
    day_end_hour: int = 21
    dry_run: bool = False


class SurfAlertResult(pydantic.BaseModel):
    good_windows: list[dict[str, Any]]
    email_sent: bool
    message: str


@workflows.activity(start_to_close_timeout=timedelta(seconds=120))
async def fetch_forecasts(spot_ids: list[str]) -> dict[str, dict[str, Any]]:
    from worker.openmeteo import fetch_spot_forecasts

    return await fetch_spot_forecasts(spot_ids)


@workflows.activity(start_to_close_timeout=timedelta(seconds=120))
async def select_windows(
    forecasts: dict[str, dict[str, Any]],
    spots_by_id: dict[str, dict[str, str]],
    min_rating: str,
    days_ahead: list[int],
    day_start_hour: int,
    day_end_hour: int,
) -> list[dict[str, Any]]:
    from worker.selection import select_good_windows

    return select_good_windows(
        forecasts,
        spots_by_id,
        now=datetime.now(timezone.utc),
        min_rating=min_rating,
        days_ahead=days_ahead,
        day_start_hour=day_start_hour,
        day_end_hour=day_end_hour,
    )


@workflows.activity(start_to_close_timeout=timedelta(seconds=120))
async def send_alert_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str,
    gmail: ToolCallClient = Depends(gmail_connector),
) -> str:
    smtp_configured = bool(
        os.environ.get("SMTP_USER") or os.environ.get("smtp_user")
    ) and bool(os.environ.get("SMTP_PASSWORD") or os.environ.get("smtp_password"))
    if smtp_configured:
        await asyncio.to_thread(
            send_email_smtp, recipient, subject, text_body, html_body
        )
        return "smtp"
    await gmail.call_tool(
        "send_email",
        {
            "to": [recipient],
            "subject": subject,
            "body": text_body,
            "htmlBody": html_body,
        },
    )
    return "gmail_connector"


@workflows.workflow.define(
    name="surfline-alerts",
    workflow_display_name="Alertes Surf Martigues–Hyères",
    workflow_description=(
        "Vérifie les prévisions Open-Meteo entre Martigues et Hyères et envoie un "
        "email lorsque les conditions de la semaine (J+1 à J+7) atteignent le rating minimal."
    ),
)
@uses_connectors(gmail_connector)
class SurfAlertWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: SurfAlertInput | None = None) -> SurfAlertResult:
        config = input or SurfAlertInput()
        spots_by_id = {spot.spot_id: {"name": spot.name, "url": spot.url} for spot in SPOTS}
        forecasts = await fetch_forecasts([spot.spot_id for spot in SPOTS])
        windows = await select_windows(
            forecasts,
            spots_by_id,
            config.min_rating,
            config.days_ahead,
            config.day_start_hour,
            config.day_end_hour,
        )
        if not windows:
            return SurfAlertResult(
                good_windows=[],
                email_sent=False,
                message="Aucune bonne condition prévue dans la semaine : pas d'email envoyé.",
            )
        subject, text_body, html_body = build_email(windows)
        if config.dry_run:
            return SurfAlertResult(
                good_windows=windows,
                email_sent=False,
                message=f"dry-run : {subject}",
            )
        await send_alert_email(config.recipient_email, subject, text_body, html_body)
        return SurfAlertResult(
            good_windows=windows,
            email_sent=True,
            message=f"Alerte envoyée à {config.recipient_email} : {subject}",
        )
