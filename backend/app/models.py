from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    verifications = relationship("ContentVerification", back_populates="owner")


class ContentVerification(Base):
    __tablename__ = "content_verifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content_type = Column(String(50), nullable=False)
    content_text = Column(Text, default="")
    source_url = Column(String(500), nullable=True)
    source_name = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")
    risk_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    verdict = Column(String(50), default="unknown")
    analysis_summary = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="verifications")
    report = relationship("VerificationReport", uselist=False, back_populates="verification")


class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(Integer, ForeignKey("content_verifications.id"), unique=True, nullable=False)
    source_credibility = Column(Float, default=0.0)
    ai_likelihood = Column(Float, default=0.0)
    manipulation_signals = Column(Text, default="")
    recommendations = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    verification = relationship("ContentVerification", back_populates="report")
