from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routes.auth import router as auth_router
from app.routes.content import router as content_router
from app.routes.dashboard import router as dashboard_router

app = FastAPI(
    title="VerifyAI API",
    description="AI content verification and trust analysis platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")

create_tables()

@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "verifyai-backend",
        "environment": settings.environment,
    }
