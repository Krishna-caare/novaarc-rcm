import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.routers import (
    auth, claims, denials, payments, dashboard,
    work_queues, agents, assistant, knowledge_graph
)


async def _async_init_db():
    try:
        await init_db()
        from app.core.database import AsyncSessionLocal
        from app.models import User
        from sqlalchemy import select, func
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(func.count(User.user_id)))
            user_count = result.scalar() or 0
            if user_count == 0:
                print("Database is empty. Running initial demo seed...")
                from scripts.seed import main as seed_main
                await seed_main()
                print("Initial seed completed successfully!")
    except Exception as e:
        print(f"Database initialization / seed notice: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Launch schema verification and auto-seed in background so Uvicorn binds port
    # and answers Render health check probes immediately without hitting 5s timeout.
    init_task = asyncio.create_task(_async_init_db())
    yield
    if not init_task.done():
        init_task.cancel()


app = FastAPI(
    title="NovaArc RCM",
    description="Revenue Cycle Management with Agentic AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Build allowed origins: always include localhost, Netlify domains, GitHub Pages, Render, plus FRONTEND_URL
_allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "https://novaarc.netlify.app",
    "https://novaarc-frontend.onrender.com",
    "https://majestic-seahorse-c3e878.netlify.app",
    "https://krishna-caare.github.io",
]

# FRONTEND_URL env var lets additional URLs be whitelisted at deploy time (comma-separated supported)
_frontend_url = os.getenv("FRONTEND_URL", "")
if _frontend_url:
    for url in _frontend_url.split(","):
        clean_url = url.strip().rstrip("/")
        if clean_url and clean_url not in _allowed_origins:
            _allowed_origins.append(clean_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=r"https://.*(\.netlify\.app|\.github\.io|\.onrender\.com)",
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
app.include_router(knowledge_graph.router, prefix="/knowledge-graph", tags=["Knowledge Graph & Vector RAG"])

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"Unhandled exception on {request.method} {request.url.path}: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb}
    )


@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"status": "healthy", "service": "novaarc-rcm", "version": "1.0.2"}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {"status": "healthy", "service": "novaarc-rcm", "version": "1.0.2"}
