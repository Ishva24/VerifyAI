from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.database import get_db
from app.models import ContentVerification, VerificationReport
from app.schemas import VerificationInput, VerificationResponse
from app.services.verifier import build_verification_result
from app.services.analytics import call_ai_service

router = APIRouter(tags=["content"])


@router.post("/verifications", response_model=VerificationResponse)
async def create_verification(payload: VerificationInput, db: Session = Depends(get_db)):
    risk_score, confidence, verdict, summary, manipulation_signals, recommendations = build_verification_result(payload.model_dump())

    verification = ContentVerification(
        title=payload.title,
        content_type=payload.content_type,
        content_text=payload.content_text,
        source_url=payload.source_url,
        source_name=payload.source_name,
        status="completed",
        risk_score=risk_score,
        confidence=confidence,
        verdict=verdict,
        analysis_summary=summary,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)

    ai_data = await call_ai_service({
        "content_type": payload.content_type,
        "content_text": payload.content_text,
        "source_url": payload.source_url,
        "source_name": payload.source_name,
    })

    report = VerificationReport(
        verification_id=verification.id,
        source_credibility=ai_data.get("source_credibility", 0.5),
        ai_likelihood=ai_data.get("ai_likelihood", 0.5),
        manipulation_signals=", ".join(manipulation_signals),
        recommendations="; ".join(recommendations),
    )
    db.add(report)
    db.commit()

    return VerificationResponse(
        id=verification.id,
        title=verification.title,
        content_type=verification.content_type,
        status=verification.status,
        risk_score=verification.risk_score,
        confidence=verification.confidence,
        verdict=verification.verdict,
        analysis_summary=verification.analysis_summary,
        source_credibility=report.source_credibility,
        ai_likelihood=report.ai_likelihood,
        manipulation_signals=manipulation_signals,
        recommendations=recommendations,
    )


@router.get("/verifications")
def list_verifications(db: Session = Depends(get_db)):
    items = db.query(ContentVerification).order_by(ContentVerification.created_at.desc()).all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "content_type": item.content_type,
            "risk_score": item.risk_score,
            "verdict": item.verdict,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]
