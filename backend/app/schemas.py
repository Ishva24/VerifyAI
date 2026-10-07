from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)
    role: str = "viewer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    role: str
    is_active: int

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerificationInput(BaseModel):
    title: str
    content_type: str = "text"
    content_text: str = ""
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    source_domain: Optional[str] = None
    priority: str = "medium"


class VerificationUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    verdict: Optional[str] = None
    analysis_summary: Optional[str] = None
    risk_score: Optional[float] = None
    confidence: Optional[float] = None


class VerificationReviewInput(BaseModel):
    verdict: str
    notes: str = ""


class VerificationResponse(BaseModel):
    id: int
    title: str
    content_type: str
    status: str
    risk_score: float = 0.0
    confidence: float = 0.0
    verdict: str = "unknown"
    analysis_summary: str = ""
    owner_id: Optional[int] = None


class VerificationReportResponse(BaseModel):
    verification_id: int
    title: str
    content_type: str
    status: str
    risk_score: float
    confidence: float
    verdict: str
    source_credibility: float
    ai_likelihood: float
    manipulation_signals: list[str]
    recommendations: list[str]
    evidence_count: int
    review_count: int
    created_at: str
    updated_at: str
