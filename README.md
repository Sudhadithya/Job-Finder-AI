# Job Finder AI

> AI-powered job discovery and matching platform for software engineers and data scientists.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Gemini](https://img.shields.io/badge/Gemini-8E75C2?style=flat-square&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

---

## What it does

Job Finder AI takes a resume PDF, parses it using Google Gemini (with a regex fallback), then scrapes live postings from Greenhouse, Lever, and Ashby job boards. It filters by role type, location, and freshness — then ranks every posting against the candidate's profile using a weighted scoring model across skills, projects, experience, role fit, and education.

Built for the Indian tech job market: currently targets Bangalore, Hyderabad, and Remote India roles for SDE-1 and Data Scientist positions.

## Architecture

```
                  ┌──────────────┐
                  │  Next.js UI  │
                  │  (React/TS)  │
                  └──────┬───────┘
                         │ REST
                  ┌──────▼───────┐
                  │   FastAPI    │
                  │   Backend    │
                  └──┬───┬───┬──┘
                     │   │   │
          ┌──────────┘   │   └──────────┐
          ▼              ▼              ▼
   ┌─────────────┐ ┌──────────┐ ┌─────────────┐
   │ Resume      │ │ Job      │ │ Matching &  │
   │ Parser      │ │ Discovery│ │ Ranking     │
   │ (Gemini +   │ │ (ATS     │ │ Engine      │
   │  Regex)     │ │  Scraper)│ │             │
   └─────────────┘ └──────────┘ └─────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         Greenhouse    Lever     Ashby
                         │
                  ┌──────▼───────┐
                  │  PostgreSQL  │
                  │ (SQLite fbk) │
                  └──────────────┘
```

## Key Features

- **Resume parsing** — Extracts skills, projects, experience, and education from PDFs via Gemini `2.5-flash` with a deterministic regex fallback.
- **Multi-board scraping** — Pulls postings from Greenhouse, Lever, Ashby, and custom career portals in parallel.
- **Smart filtering** — Classifies roles (SDE-1 / Data Scientist), validates locations, filters out senior/lead/manager titles, and enforces a 15-day freshness window.
- **Weighted scoring** — Ranks matches on a 0–100 scale: skill match (45%), project relevance (25%), experience (15%), role alignment (10%), education (5%).
- **Explainable results** — Each match includes matching skills, missing skills, and AI-generated reasoning.
- **Resilient by default** — Auto-falls back to SQLite if Postgres is down. Throttles LLM calls via semaphores. Skips recently-failed boards for 24h.

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, React 19, TypeScript |
| Backend | FastAPI, SQLAlchemy, HTTPX/AIOHTTP |
| AI | Google Gemini API (`gemini-2.5-flash`) |
| Database | PostgreSQL 16 (SQLite fallback) |
| PDF | PyMuPDF (`fitz`) |
| Infra | Docker Compose |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/            # Route handlers
│   │   ├── core/           # Config & DB init
│   │   ├── jobsources/     # ATS scrapers (Greenhouse, Lever, Ashby)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (parsing, discovery, matching)
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router pages
│   │   ├── components/     # React components
│   │   ├── lib/            # API client
│   │   └── types/          # TypeScript interfaces
│   └── package.json
└── docker-compose.yml
```

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker (optional — for PostgreSQL)

### Setup

```bash
# Clone
git clone https://github.com/Sudhadithya/Job-Finder-AI.git
cd Job-Finder-AI

# Environment variables
cp .env.example backend/.env
cp .env.example frontend/.env.local
# Edit backend/.env → set GEMINI_API_KEY and DATABASE_URL
# Edit frontend/.env.local → set NEXT_PUBLIC_API_URL=http://localhost:8000

# Database (optional — skip if you're fine with SQLite)
docker compose up -d

# Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Backend docs: [http://localhost:8000/docs](http://localhost:8000/docs)
App: [http://localhost:3000](http://localhost:3000)

## Roadmap

- [x] Greenhouse, Lever, Ashby scrapers
- [x] Gemini-powered resume parsing with regex fallback
- [x] Location filtering (Bangalore, Hyderabad, Remote India)
- [x] Multi-criteria ranking engine
- [x] SQLite auto-fallback
- [ ] Additional role categories (PM, DevOps)
- [ ] Scheduled discovery (cron-based)
- [ ] Application tracking (Applied → Interviewing → Offered)
- [ ] Resume optimization suggestions
- [ ] AI-generated interview prep

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit and push
4. Open a PR

## License

MIT
