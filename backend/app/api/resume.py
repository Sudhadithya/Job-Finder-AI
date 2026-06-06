import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Resume
from app.api.profile import get_default_user
from app.services.parser import parse_resume_pdf
from app.schemas.schemas import ResumeUploadResponse

router = APIRouter(prefix="/api/resume", tags=["resume"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
        
    user = get_default_user(db)
    
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{user.id}_{file.filename}")
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
        
    # Parse resume
    parsed_json = parse_resume_pdf(file_path)
    
    # Save/Update in DB
    existing_resume = db.query(Resume).filter_by(user_id=user.id).first()
    if existing_resume:
        existing_resume.resume_url = file_path
        existing_resume.parsed_json = parsed_json
    else:
        new_resume = Resume(
            user_id=user.id,
            resume_url=file_path,
            parsed_json=parsed_json
        )
        db.add(new_resume)
        
    # Extract email and update user profile if found
    extracted_email = parsed_json.get("email")
    if extracted_email:
        user.email = extracted_email
        
    db.commit()
    
    # Get resume ID
    resume_db = db.query(Resume).filter_by(user_id=user.id).first()
    
    return ResumeUploadResponse(
        resume_id=resume_db.id,
        skills=parsed_json.get("skills", []),
        projects=parsed_json.get("projects", []),
        experience=parsed_json.get("experience", []),
        education=parsed_json.get("education", []),
        metrics=parsed_json.get("metrics")
    )
