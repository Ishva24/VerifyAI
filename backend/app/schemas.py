from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class VerificationInput(BaseModel):
    title: str
    content_type: str = "text"
    content_text: str = ""
    source_url: Optional[str] = None
    source_name: Optional[str] = None


class VerificationResponse(BaseModel):
    id: int
    title: str
    content_type: str
    status: str
    risk_score: float
    confidence: float
    verdict: str
    analysis_summary: str
    source_credibility: float
    ai_likelihood: float
    manipulation_signals: list[str]
    recommendations: list[str]
