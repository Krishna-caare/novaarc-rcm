import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.routers import (
    auth, claims, denials, payments, dashboard,
    work_queues, agents, assistant
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="NovaArc RCM",
    description="Revenue Cycle Management with Agentic AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Build allowed origins: always include localhost, plus any production URLs
_allowed_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

# FRONTEND_URL env var lets Railway/Netlify URLs be whitelisted at deploy time
# e.g. FRONTEND_URL=https://novaarc.netlify.app
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    _allowed_origins.append(_frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(claims.router, prefix="/claims", tags=["Claims"])
app.include_router(denials.router, prefix="/denials", tags=["Denials"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(work_queues.router, prefix="/work-queues", tags=["Work Queues"])
app.include_router(agents.router, prefix="/agents", tags=["Agents"])
app.include_router(assistant.router, prefix="/assistant", tags=["AI Assistant"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "novaarc-rcm"}