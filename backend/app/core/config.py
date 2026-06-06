import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Job Finder AI"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+pg8000://postgres:postgres@localhost:5432/jobfinder")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()
