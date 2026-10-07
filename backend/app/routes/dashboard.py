from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContentVerification, User

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total = db.query(ContentVerification).count()
    low_risk = db.query(ContentVerification).filter(ContentVerification.verdict == "low_risk").count()
    flagged = db.query(ContentVerification).filter(ContentVerification.verdict == "likely_malicious").count()
    review = db.query(ContentVerification).filter(ContentVerification.verdict == "requires_review").count()
    users = db.query(User).count()

    return {
        "summary": {
            "total_verifications": total,
            "low_risk": low_risk,
            "flagged": flagged,
            "requires_review": review,
            "active_users": users,
        },
        "recent_activity": [
            {
                "title": v.title,
                "verdict": v.verdict,
                "risk_score": v.risk_score,
                "created_at": v.created_at.isoformat(),
            }
            for v in db.query(ContentVerification).order_by(ContentVerification.created_at.desc()).limit(5).all()
        ],
    }
