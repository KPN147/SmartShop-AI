"""
SmartShop AI - FastAPI Application Entry Point
"""

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Load .env before importing other modules
load_dotenv()

from routers.chat import router as chat_router
from routers.products import router as products_router
from services.rag_service import get_rag_service
from models.schemas import HealthResponse

# ===== Logging Setup =====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ===== Lifespan (startup/shutdown) =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown."""
    logger.info("🚀 SmartShop AI Backend is starting...")
    
    # Validate API Keys
    llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if llm_provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️  OPENAI_API_KEY is not configured!")
    elif llm_provider == "gemini" and not os.getenv("GOOGLE_API_KEY"):
        logger.warning("⚠️  GOOGLE_API_KEY is not configured!")
    
    # Pre-initialize RAG service (index documents on startup)
    try:
        rag = get_rag_service(
            llm_provider=llm_provider,
            model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini") if llm_provider == "openai" else os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        )
        await rag.initialize()
        logger.info("✅ RAG Service initialized successfully!")
    except Exception as e:
        logger.error(f"❌ Error initializing RAG Service: {e}")
    
    logger.info("✅ SmartShop AI Backend is ready!")
    
    yield  # Application is running
    
    logger.info("👋 SmartShop AI Backend is shutting down...")


# ===== FastAPI App =====
app = FastAPI(
    title="SmartShop AI API",
    description="Multi-Agent AI E-commerce Chatbot - Automated Sales and Customer Care",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ===== CORS Middleware =====
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Request Timing Middleware =====
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration:.1f}"
    return response

# ===== Exception Handler =====
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)}
    )

# ===== Routes =====
app.include_router(chat_router, prefix="/api/v1")
app.include_router(products_router, prefix="/api/v1")

@app.get("/", summary="Root", include_in_schema=False)
async def root():
    return {"message": "SmartShop AI API v1.0.0 🚀", "docs": "/docs"}

@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health Check",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    """Check API and services status."""
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    openai_key = bool(os.getenv("OPENAI_API_KEY"))
    gemini_key = bool(os.getenv("GOOGLE_API_KEY"))
    
    return HealthResponse(
        status="ok",
        version="1.0.0",
        services={
            "llm_provider": llm_provider,
            "openai_configured": openai_key,
            "gemini_configured": gemini_key,
            "rag": "ready",
            "sentiment": "keyword-based (ready)",
        }
    )
