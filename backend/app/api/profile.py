from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import User
from app.schemas.schemas import UserProfileResponse, UserUpdateCategory

router = APIRouter(prefix="/api/profile", tags=["profile"])

def get_default_user(db: Session) -> User:
    user = db.query(User).first()
    if not user:
        user = User(email="candidate@example.com", desired_category="SDE-1")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.get("", response_model=UserProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    user = get_default_user(db)
    return user

@router.post("/category", response_model=UserProfileResponse)
def update_category(data: UserUpdateCategory, db: Session = Depends(get_db)):
    user = get_default_user(db)
    user.desired_category = data.category
    db.commit()
    db.refresh(user)
    return user
