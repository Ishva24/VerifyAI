import asyncio
from datetime import datetime

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import ContentVerification, VerificationReport, VerificationStatus
from app.services.verifier import build_verification_result, call_ai_service


async def process_verification_job(verification_id: int, payload: dict) -> None:
    """Background job to process verification request asynchronously."""
    db: Session = SessionLocal()
    try:
        verification = db.query(ContentVerification).filter(ContentVerification.id == verification_id).first()
        if not verification:
            return

        verification.status = VerificationStatus.processing.value
        db.commit()

        risk_score, confidence, verdict, summary, manipulation_signals, recommendations = build_verification_result(
            payload
        )

        ai_data = await call_ai_service(payload)

        report = db.query(VerificationReport).filter(VerificationReport.verification_id == verification_id).first()
        if not report:
            report = VerificationReport(verification_id=verification_id)
            db.add(report)

        report.source_credibility = ai_data.get("source_credibility", 0.5)
        report.ai_likelihood = ai_data.get("ai_likelihood", 0.5)
        report.manipulation_signals = ", ".join(manipulation_signals)
        report.recommendations = "; ".join(recommendations)

        verification.risk_score = risk_score
        verification.confidence = confidence
        verification.verdict = verdict
        verification.analysis_summary = summary
        verification.status = VerificationStatus.needs_review.value if verdict != "low_risk" else VerificationStatus.verified.value
        verification.completed_at = datetime.utcnow()

        db.commit()
    except Exception as e:
        print(f"Error processing verification {verification_id}: {e}")
        verification.status = VerificationStatus.queued.value
        db.commit()
    finally:
        db.close()


def enqueue_verification_job(verification_id: int, job_id: str, payload: dict) -> None:
    """Enqueue a verification job for background processing."""
    asyncio.create_task(process_verification_job(verification_id, payload))
