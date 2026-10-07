from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models import (
    ContentVerification,
    User,
    VerificationEvidence,
    VerificationReport,
    VerificationReview,
    VerificationStatus,
)
from app.schemas import (
    VerificationInput,
    VerificationResponse,
    VerificationUpdate,
    VerificationReviewInput,
    VerificationReportResponse,
)
from app.services.verifier import build_verification_result, call_ai_service
from app.services.jobs import enqueue_verification_job

router = APIRouter(tags=["content"])
UPLOAD_ROOT = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


@router.post("/verifications", response_model=VerificationResponse)
async def create_verification(
    payload: VerificationInput,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a verification request and queue it for processing."""
    verification = ContentVerification(
        title=payload.title,
        content_type=payload.content_type,
        content_text=payload.content_text,
        source_url=payload.source_url,
        source_name=payload.source_name,
        source_domain=payload.source_domain,
        priority=payload.priority,
        owner_id=current_user.id,
        status=VerificationStatus.queued.value,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)

    job_id = str(uuid4())
    verification.job_id = job_id
    db.commit()

    background_tasks.add_task(
        enqueue_verification_job,
        verification_id=verification.id,
        job_id=job_id,
        payload=payload.model_dump(),
    )

    return VerificationResponse(
        id=verification.id,
        title=verification.title,
        content_type=verification.content_type,
        status=verification.status,
        risk_score=verification.risk_score,
        confidence=verification.confidence,
        verdict=verification.verdict,
        analysis_summary=verification.analysis_summary,
        owner_id=current_user.id,
    )


@router.post("/verifications/upload", response_model=VerificationResponse)
async def upload_verification(
    title: str = Form(...),
    content_type: str = Form("image"),
    source_url: Optional[str] = Form(None),
    source_name: Optional[str] = Form(None),
    source_domain: Optional[str] = Form(None),
    priority: str = Form("medium"),
    file: Optional[UploadFile] = File(None),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload media for verification and queue async processing."""
    uploaded_filename = file.filename if file and file.filename else ""
    storage_path = None
    evidence_type = "media"
    file_size = 0

    if file and file.filename:
        file_ext = Path(file.filename).suffix
        safe_name = f"{uuid4().hex}{file_ext}"
        verification_dir = UPLOAD_ROOT / f"verification_{uuid4().hex}"
        verification_dir.mkdir(parents=True, exist_ok=True)
        storage_path = verification_dir / safe_name
        contents = await file.read()
        storage_path.write_bytes(contents)
        file_size = len(contents)

    verification = ContentVerification(
        title=title,
        content_type=content_type,
        content_text=f"Uploaded file: {uploaded_filename}",
        source_url=source_url,
        source_name=source_name,
        source_domain=source_domain,
        priority=priority,
        owner_id=current_user.id,
        status=VerificationStatus.queued.value,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)

    if storage_path:
        evidence = VerificationEvidence(
            verification_id=verification.id,
            file_name=uploaded_filename,
            storage_path=str(storage_path),
            evidence_type=evidence_type,
            file_size=file_size,
        )
        db.add(evidence)

    job_id = str(uuid4())
    verification.job_id = job_id
    db.commit()

    background_tasks.add_task(
        enqueue_verification_job,
        verification_id=verification.id,
        job_id=job_id,
        payload={
            "title": title,
            "content_type": content_type,
            "content_text": verification.content_text,
            "source_url": source_url,
            "source_name": source_name,
            "source_domain": source_domain,
            "priority": priority,
            "file_path": str(storage_path) if storage_path else None,
        },
    )

    return VerificationResponse(
        id=verification.id,
        title=verification.title,
        content_type=verification.content_type,
        status=verification.status,
        risk_score=verification.risk_score,
        confidence=verification.confidence,
        verdict=verification.verdict,
        analysis_summary=verification.analysis_summary,
        owner_id=current_user.id,
    )


@router.get("/verifications")
def list_verifications(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List verifications with optional filtering."""
    query = db.query(ContentVerification).order_by(ContentVerification.created_at.desc())

    if current_user.role != "admin":
        query = query.filter(ContentVerification.owner_id == current_user.id)

    if status_filter:
        query = query.filter(ContentVerification.status == status_filter)

    items = query.all()

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
def get_verification(
    verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get full verification details including report and reviews."""
    item = db.query(ContentVerification).filter(ContentVerification.id == verification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")
    if current_user.role != "admin" and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this verification")

    report = db.query(VerificationReport).filter(VerificationReport.verification_id == verification_id).first()
    reviews = db.query(VerificationReview).filter(VerificationReview.verification_id == verification_id).all()

    return {
        "id": item.id,
        "title": item.title,
        "content_type": item.content_type,
        "status": item.status,
        "priority": item.priority,
        "risk_score": item.risk_score,
        "confidence": item.confidence,
        "verdict": item.verdict,
        "analysis_summary": item.analysis_summary,
        "source_credibility": report.source_credibility if report else 0.0,
        "ai_likelihood": report.ai_likelihood if report else 0.0,
        "manipulation_signals": report.manipulation_signals.split(", ") if report else [],
        "recommendations": report.recommendations.split("; ") if report else [],
        "evidence_count": len(item.evidence),
        "reviews": [
            {
                "id": r.id,
                "reviewer_name": r.reviewer.name,
                "status": r.status,
                "verdict": r.verdict,
                "notes": r.notes,
                "created_at": r.created_at.isoformat(),
            }
            for r in reviews
        ],
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


@router.patch("/verifications/{verification_id}")
def update_verification(
    verification_id: int,
    payload: VerificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Update verification metadata and status."""
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


@router.post("/verifications/{verification_id}/reviews")
def submit_review(
    verification_id: int,
    payload: VerificationReviewInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Submit a review for a verification."""
    item = db.query(ContentVerification).filter(ContentVerification.id == verification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")

    review = VerificationReview(
        verification_id=verification_id,
        reviewer_id=current_user.id,
        status="submitted",
        verdict=payload.verdict,
        notes=payload.notes,
    )
    db.add(review)

    if payload.verdict:
        item.verdict = payload.verdict
        item.status = VerificationStatus.verified.value if payload.verdict != "rejected" else VerificationStatus.rejected.value

    db.commit()
    db.refresh(review)

    return {
        "id": review.id,
        "verification_id": verification_id,
        "reviewer_name": current_user.name,
        "verdict": review.verdict,
        "notes": review.notes,
        "created_at": review.created_at.isoformat(),
    }


@router.get("/verifications/{verification_id}/report", response_model=VerificationReportResponse)
def get_verification_report(
    verification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get full verification report."""
    item = db.query(ContentVerification).filter(ContentVerification.id == verification_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Verification not found")
    if current_user.role != "admin" and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this report")

    report = db.query(VerificationReport).filter(VerificationReport.verification_id == verification_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    evidence = db.query(VerificationEvidence).filter(VerificationEvidence.verification_id == verification_id).all()
    reviews = db.query(VerificationReview).filter(VerificationReview.verification_id == verification_id).all()

    return VerificationReportResponse(
        verification_id=verification_id,
        title=item.title,
        content_type=item.content_type,
        status=item.status,
        risk_score=item.risk_score,
        confidence=item.confidence,
        verdict=item.verdict,
        source_credibility=report.source_credibility,
        ai_likelihood=report.ai_likelihood,
        manipulation_signals=report.manipulation_signals.split(", "),
        recommendations=report.recommendations.split("; "),
        evidence_count=len(evidence),
        review_count=len(reviews),
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )
