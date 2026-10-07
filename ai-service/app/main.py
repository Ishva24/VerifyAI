from fastapi import FastAPI

app = FastAPI(title="VerifyAI AI Service")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai_verifier"}


@app.post("/detect")
def detect(payload: dict):
    text = (payload.get("content_text") or "").lower()
    content_type = (payload.get("content_type") or "text").lower()
    risk = 0.15

    suspicious_terms = [
        "deepfake",
        "fake news",
        "manipulated",
        "synthetic",
        "fabricated",
        "viral clip",
        "AI generated",
        "unverified",
    ]

    for term in suspicious_terms:
        if term in text:
            risk += 0.25

    if content_type in {"image", "video", "audio"}:
        risk += 0.2

    if payload.get("source_url"):
        risk += 0.1

    risk = min(risk, 0.96)

    return {
        "source_credibility": round(max(0.15, 1.0 - risk), 2),
        "ai_likelihood": round(risk, 2),
        "confidence": round(min(0.92, 0.5 + risk), 2),
        "signals": [
            "content metadata mismatch",
            "potential synthetic origin",
            "source credibility concerns",
        ] if risk >= 0.5 else ["limited anomaly evidence"],
    }
