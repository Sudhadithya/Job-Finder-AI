import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, UniqueConstraint, func, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    desired_category = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resume_url = Column(String, nullable=False)
    parsed_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="resumes")


class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True) # e.g. "greenhouse:12345"
    role = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    source = Column(String, nullable=False)
    job_url = Column(String, nullable=False)
    description = Column(String, nullable=False)
    posted_at = Column(DateTime, nullable=True)
    min_requirements = Column(JSON, nullable=True)
    preferred_requirements = Column(JSON, nullable=True)
    discovered_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    matches = relationship("Match", back_populates="job", cascade="all, delete-orphan")


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String, ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    matching_skills = Column(JSON, nullable=False)
    missing_skills = Column(JSON, nullable=False)
    reasoning = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Unique constraint per user/job
    __table_args__ = (
        UniqueConstraint('user_id', 'job_id', name='unique_user_job_match'),
    )
    
    # Relationships
    user = relationship("User", back_populates="matches")
    job = relationship("Job", back_populates="matches")


class DiscoveredCompany(Base):
    __tablename__ = "discovered_companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    board_type = Column(String, nullable=False) # "greenhouse", "lever", "ashby"
    board_id = Column(String, unique=True, nullable=False) # e.g. "stripe", "palantir"
    discovered_at = Column(DateTime, server_default=func.now())
    last_failed_at = Column(DateTime, nullable=True)  # tracks last 404/403/410 to skip recently failed boards

