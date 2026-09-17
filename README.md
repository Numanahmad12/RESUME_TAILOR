# ResumeAI — AI-Powered Resume Tailoring Engine with RAG Pipeline

An AI-powered resume tailoring engine with a **RAG (Retrieval-Augmented Generation)** pipeline that uses sentence-transformers embeddings + Gemini LLM to create perfectly tailored resumes for any job description.

## Architecture

- **Frontend**: Next.js 14 (React 18, Tailwind CSS, Framer Motion)
- **Backend**: FastAPI (Python 3.12+)
- **Pipeline**: parse → RAG embed → retrieve → LLM draft → LaTeX → PDF
- **RAG Pipeline**: sentence-transformers embeddings + in-memory vector store + Gemini LLM
- **Output**: PDF (WeasyPrint HTML→PDF), LaTeX source, Markdown
- **LLM**: Google Gemini (gemini-1.5-flash) with RAG context retrieval

## New RAG Pipeline (Recommended)

The pipeline now uses a **Retrieval-Augmented Generation** approach:

1. **Extract** — Parse resume (PDF/DOCX) and JD into structured data
2. **Embed** — Use `sentence-transformers` (`all-MiniLM-L6-v2`) to create embeddings of all resume sections and JD requirements
3. **Retrieve** — Perform cosine similarity search to find the most relevant chunks from the resume and JD
4. **Augment** — Build a comprehensive prompt with retrieved RAG context
5. **Draft** — Send to Gemini LLM to draft a completely new, tailored resume in markdown
6. **Convert** — Convert markdown → styled HTML → PDF (via WeasyPrint) or LaTeX source

### RAG Pipeline Endpoint

```
POST /api/rag-pipeline
Body: { resume_id, jd_id, format: "pdf" | "latex" | "markdown", top_k: 8 }
Response: PDF file or LaTeX source
```

### Legacy Pipeline (Still Available)

```
POST /api/generate-tailored  # Legacy LLM pipeline (kept for backward compatibility)
POST /api/rag-pipeline/status  # Check RAG pipeline availability
```

## Local Development

### Backend

```bash
# From repo root
$env:PYTHONPATH="backend/src;."; python -m uvicorn backend.src.api.app:app --host 127.0.0.1 --port 8000
```

The backend uses relative imports (`from ..services...`), so `backend/src` needs to be on `PYTHONPATH`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend proxies `/api/*` → `http://localhost:8000/api/*`.

### Environment Setup

Copy `.env.example` to `.env` and add your Gemini API key:

```bash
cp .env.example .env
# Edit .env and add: GEMINI_API_KEY=AIzaSy...
```

## Dependencies

All Python dependencies are in `requirements.txt`. Key new additions:
- `weasyprint` — HTML→PDF rendering (replaces xelatex/pdflatex)
- `sentence-transformers` — RAG embeddings
- `pgvector` — Vector database (optional, for production)
- `google-generativeai` — Gemini LLM client
- `markdown` — Markdown→HTML conversion

## Pipeline Stages

1. **Ingestion** — PDF and DOCX parsing with structure recovery
2. **RAG Embedding** — Sentence-transformers create vector embeddings of resume sections and JD
3. **Context Retrieval** — Cosine similarity search finds top-k relevant chunks
4. **LLM Drafting** — Gemini generates a new resume using RAG-augmented prompt
5. **PDF Conversion** — Markdown→HTML→PDF via WeasyPrint
6. **Export** — Download PDF, LaTeX, or Markdown output
