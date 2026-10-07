from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import ContentVerification, User

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "admin":
        verifications = db.query(ContentVerification).order_by(ContentVerification.created_at.desc()).all()
    else:
        verifications = (
            db.query(ContentVerification)
            .filter(ContentVerification.owner_id == current_user.id)
            .order_by(ContentVerification.created_at.desc())
            .all()
        )

    total = len(verifications)
    low_risk = sum(1 for v in verifications if v.verdict == "low_risk")
    flagged = sum(1 for v in verifications if v.verdict == "likely_malicious")
    review = sum(1 for v in verifications if v.verdict == "requires_review")

    return {
        "summary": {
            "total_verifications": total,
            "low_risk": low_risk,
            "flagged": flagged,
            "requires_review": review,
            "active_users": 1 if current_user else 0,
        },
        "recent_activity": [
            {
                "title": v.title,
                "verdict": v.verdict,
                "risk_score": v.risk_score,
                "created_at": v.created_at.isoformat(),
            }
            for v in verifications[:5]
        ],
    }
