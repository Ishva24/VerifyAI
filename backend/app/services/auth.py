from typing import Any

import httpx

from app.config import settings


async def call_ai_service(payload: dict[str, Any]) -> dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{settings.ai_service_url}/detect", json=payload, timeout=20)
        response.raise_for_status()
        return response.json()


def build_verification_result(payload: dict[str, Any]) -> tuple[float, float, str, str, list[str], list[str]]:
    text = (payload.get("content_text") or "").lower()
    source_url = payload.get("source_url") or ""
    source_name = payload.get("source_name") or ""
    source_domain = payload.get("source_domain") or ""

    suspicious_markers = [
        "deepfake",
        "fake news",
        "manipulated",
        "synthetic",
        "fabricated",
        "off-platform",
        "viral clip",
        "unverified",
        "AI generated",
    ]

    risk_score = 0.12
    if any(marker in text for marker in suspicious_markers):
        risk_score += 0.35
    if len(text) > 300:
        risk_score += 0.15
    if "video" in (payload.get("content_type") or "").lower():
        risk_score += 0.15
    if source_url:
        risk_score += 0.1
    if source_name and "trusted" not in source_name.lower():
        risk_score += 0.08
    if source_domain and "trusted" not in source_domain.lower():
        risk_score += 0.05

    risk_score = min(risk_score, 0.96)
    confidence = round(min(0.55 + (risk_score * 0.4), 0.99), 2)

    if risk_score >= 0.65:
        verdict = "likely_malicious"
        summary = "This content shows high-risk signals associated with manipulated or synthetic media."
    elif risk_score >= 0.38:
        verdict = "requires_review"
        summary = "This content includes moderate uncertainty and should be reviewed by a human verifier."
    else:
        verdict = "low_risk"
        summary = "This content appears generally credible with limited suspicious indicators."

    manipulation_signals: list[str] = []
    if any(marker in text for marker in suspicious_markers):
        manipulation_signals.append("suspicious language cues")
    if payload.get("content_type") in {"image", "video", "audio"}:
        manipulation_signals.append("multi-modal media pattern")
    if source_url:
        manipulation_signals.append("external link/source dependency")
    if not manipulation_signals:
        manipulation_signals.append("limited anomaly evidence")

    recommendations = [
        "Cross-check original source metadata and timestamps.",
        "Validate with independent trusted fact-checking tools.",
        "Use reverse-image or audio verification when media is involved.",
    ]

    return round(risk_score, 2), confidence, verdict, summary, manipulation_signals, recommendations
