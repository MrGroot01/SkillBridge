from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import routers correctly
from src.routes import auth, batches, sessions, attendance, summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create DB tables on startup"""
    from src.core.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    lifespan=lifespan,
    title="SkillBridge Attendance Management API",
    description="REST API for SkillBridge attendance system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (for React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ REGISTER ROUTERS (NO PREFIX HERE)
app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(summary.router)


# Custom 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


# Health routes
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "SkillBridge Attendance API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}