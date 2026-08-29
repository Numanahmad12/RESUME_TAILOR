# ResumeAI — AI-Powered Resume Tailoring Engine

An 8-stage AI pipeline that scores, generates, validates, and renders a perfectly tailored resume for any job description — with zero hallucinations.

## Architecture

- **Frontend**: Next.js 14 (React 18, Tailwind CSS, Framer Motion, GSAP, react-three-fiber)
- **Backend**: FastAPI (Python 3.12+)
- **Pipeline**: parse → analyze JD → compute match → generate patches → validate → review → render → export
- **Output**: DOCX (python-docx) and PDF (PyMuPDF) with WeasyPrint + HTML fallback

## Local Development

### Backend

```bash
# From repo root
PYTHONPATH="backend/src:." python -m uvicorn backend.src.api.app:app --reload --port 8000
```

The backend uses **relative imports** (`from ..services...`), so the project root and `backend/src` both need to be on `PYTHONPATH` to resolve the `common/` shared schema package.

### Frontend

```bash
cd frontend
npm install
npm run dev   # development with HMR
# or
npm run build && npm run start  # production
```

The frontend proxies `/api/*` → `http://localhost:8000/api/*` (configured in `frontend/next.config.js`).

## Deployment

See `DEPLOY.md` for the Vercel + GitHub deployment steps.

## Project Structure

```
.
├── backend/
│   ├── src/
│   │   ├── api/app.py          # FastAPI endpoints
│   │   ├── services/           # Pipeline services
│   │   │   ├── resume_parser.py
│   │   │   ├── jd_analyzer.py
│   │   │   ├── gap_analyzer.py
│   │   │   ├── generator.py
│   │   │   ├── validator.py
│   │   │   └── renderer.py
│   │   └── models/resume.py    # Pydantic schemas
│   └── tests/
├── common/                     # Shared schema (used by backend)
│   └── schema/resume.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx       # Landing page
│   │   │   ├── tool.tsx        # Resume tailoring tool
│   │   │   └── api/            # API proxy routes
│   │   ├── components/
│   │   │   ├── ResumeTailorForm.tsx
│   │   │   └── landing/        # Landing page sections
│   │   ├── styles/globals.css
│   │   └── hooks/
│   ├── package.json
│   └── next.config.js
├── scripts/                    # Test scripts
├── vercel.json                 # Vercel config
└── README.md
```

## Pipeline Stages

1. **Ingestion** — PDF and DOCX parsing with structure recovery (tables, bullet lists, section headers)
2. **JD Analysis** — Required vs. preferred skills, years of experience, and responsibilities
3. **Gap Analysis** — Five sub-scores: keyword coverage, experience fit, responsibility alignment, impact, formatting
4. **Generation** — Heuristic patch generator rewrites the summary, reorders skills, upgrades weak bullets
5. **Validation** — Every patch is checked against the original resume
6. **Review** — Side-by-side diff. Accept, edit, or reject before commit
7. **Rendering** — Clean DOCX and PDF output
8. **Export** — Download the tailored resume
