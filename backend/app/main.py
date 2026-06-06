from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base, SessionLocal
from sqlalchemy import text
from app.api import profile, resume, jobs
from app.services.discovery import seed_companies_if_empty

# Create tables
Base.metadata.create_all(bind=engine)

# Dynamic self-healing migration for requirements columns
try:
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN min_requirements JSON"))
        except Exception:
            pass
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN preferred_requirements JSON"))
        except Exception:
            pass
except Exception as e:
    print(f"Migration details: {e}")

app = FastAPI(
    title="Job Finder AI API",
    description="Backend API for location-first developer job discovery and resume matching.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(profile.router)
app.include_router(resume.router)
app.include_router(jobs.router)

@app.on_event("startup")
def startup_event():
    # Seed companies on startup
    db = SessionLocal()
    try:
        seed_companies_if_empty(db)
    finally:
        db.close()

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Location-First Job Finder AI API!",
        "status": "online"
    }
