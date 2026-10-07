from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import ContentVerification, VerificationReport, User
from app.schemas import VerificationInput, VerificationResponse, VerificationUpdate
from app.services.verifier import build_verification_result, call_ai_service

router = APIRouter(tags=["content"])


@router.post("/verifications", response_model=VerificationResponse)
async def create_verification(
    payload: VerificationInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    risk_score, confidence, verdict, summary, manipulation_signals, recommendations = build_verification_result(
        payload.model_dump()
    )

    verification = ContentVerification(
        title=payload.title,
        content_type=payload.content_type,
        content_text=payload.content_text,
        source_url=payload.source_url,
        source_name=payload.source_name,
        source_domain=payload.source_domain,
        priority=payload.priority,
        owner_id=current_user.id,
        status="queued",
        risk_score=risk_score,
        confidence=confidence,
        verdict=verdict,
        analysis_summary=summary,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)

    ai_data = await call_ai_service(
        {
            "content_type": payload.content_type,
            "content_text": payload.content_text,
            "source_url": payload.source_url,
            "source_name": payload.source_name,
            "source_domain": payload.source_domain,
        }
    )

    report = VerificationReport(
        verification_id=verification.id,
        source_credibility=ai_data.get("source_credibility", 0.5),
        ai_likelihood=ai_data.get("ai_likelihood", 0.5),
        manipulation_signals=", ".join(manipulation_signals),
        recommendations="; ".join(recommendations),
    )
    db.add(report)
    verification.status = "needs_review" if verdict != "low_risk" else "verified"
    db.commit()
    db.refresh(verification)

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
        owner_id=current_user.id,
    )


@router.get("/verifications")
def list_verifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        items = db.query(ContentVerification).order_by(ContentVerification.created_at.desc()).all()
    else:
        items = (
            db.query(ContentVerification)
            .filter(ContentVerification.owner_id == current_user.id)
            .order_by(ContentVerification.created_at.desc())
            .all()
        )

    return [
        {
            "id": item.id,
            "title": item.title,
            "content_type": item.content_type,
            "risk_score": item.risk_score,
            "verdict": item.verdict,
            "status": item.status,
            "priority": item.priority,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


@router.get("/verifications/{verification_id}")
def get_verification(verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = db.query(ContentVerification).filter(ContentVerification.id == verification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")
    if current_user.role != "admin" and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this verification")
    return item


@router.patch("/verifications/{verification_id}")
def update_verification(
    verification_id: int,
    payload: VerificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    item = db.query(ContentVerification).filter(ContentVerification.id == verification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")
    if payload.status:
        item.status = payload.status
    if payload.priority:
        item.priority = payload.priority
    if payload.verdict:
        item.verdict = payload.verdict
    if payload.analysis_summary:
        item.analysis_summary = payload.analysis_summary
    if payload.risk_score is not None:
        item.risk_score = payload.risk_score
    if payload.confidence is not None:
        item.confidence = payload.confidence
    db.commit()
    db.refresh(item)
    return item
