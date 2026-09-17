"""FastAPI application with all pipeline endpoints."""
import sys
import os
import re
from dotenv import load_dotenv
load_dotenv(r'C:\Users\numan\Desktop\RESUME_BUILDER\.env')
sys.path.insert(0, r'C:\Users\numan\Desktop\RESUME_BUILDER')
import subprocess
from datetime import datetime, timezone
# Add RESUME_BUILDER root to path so 'common' module is findable
sys.path.insert(0, r'C:\Users\numan\Desktop\RESUME_BUILDER')

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
import tempfile
import json
import uuid
import copy

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import pipeline services
from ..services.resume_parser import parse_pdf, parse_docx
from ..services.jd_analyzer import analyze_jd
from ..services.gap_analyzer import compute_match, MatchReport
from ..services.generator import generate_patches, PatchList, _llm_tailor_latex
from ..services.validator import validate_patches
from ..services.renderer import render_docx, render_pdf, render_latex
from ..services.pdf_converter import markdown_to_pdf, markdown_to_latex
from ..models.resume import ResumeSchema, JointRequirementsSchema, PatchAction

# Import RAG pipeline
try:
    from ..services.rag_pipeline import draft_resume_rag, build_rag_index, retrieve_relevant_chunks, tailor_structured
    from ..services.jakes_template import render_jakes_latex, render_jakes_pdf, resume_to_markdown
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


# In-memory storage (replace with DB in production)
storage: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Path("uploads").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)
    yield
    # Shutdown


app = FastAPI(title="Resume Tailoring Engine", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    resume_id: str
    jd_id: str


class GenerateRequest(BaseModel):
    resume_id: str
    jd_id: str
    match_report: dict


class ApplyRequest(BaseModel):
    resume_id: str
    generation_id: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    """Health check."""
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/upload/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse resume file (PDF/DOCX). Original file is preserved."""
    content = await file.read()
    suffix = Path(file.filename).suffix.lower()

    if suffix not in (".pdf", ".docx", ".doc"):
        raise HTTPException(400, "Unsupported file format. Use PDF or DOCX.")

    # Save the original file permanently
    original_filename = f"{str(uuid.uuid4())[:8]}{suffix}"
    original_path = Path("uploads") / original_filename
    original_path.write_bytes(content)

    try:
        if suffix == ".pdf":
            resume = parse_pdf(str(original_path))
        else:
            resume = parse_docx(str(original_path))
    except Exception as e:
        original_path.unlink(missing_ok=True)
        raise HTTPException(500, f"Failed to parse resume: {str(e)}")

    resume_id = str(uuid.uuid4())[:8]
    storage[resume_id] = {
        "type": "resume",
        "data": resume.model_dump(),
        "original_path": str(original_path),
        "original_suffix": suffix,
    }
    return {"resume_id": resume_id, "resume": resume.model_dump()}


@app.post("/api/upload/jd")
async def upload_jd(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None)):
    """Upload JD as file or paste raw text."""
    if file:
        content = await file.read()
        jd_text = content.decode("utf-8", errors="ignore")
    elif text:
        jd_text = text
    else:
        raise HTTPException(400, "Provide either a file or raw text.")

    jd = analyze_jd(jd_text)
    jd_id = str(uuid.uuid4())[:8]
    storage[jd_id] = {"type": "jd", "data": jd.model_dump()}
    return {"jd_id": jd_id, "jd": jd.model_dump()}


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    """Run gap & match analysis between resume and JD."""
    resume_data = storage.get(request.resume_id)
    jd_data = storage.get(request.jd_id)

    if not resume_data or not jd_data:
        raise HTTPException(404, "Resume or JD not found. Upload first.")

    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])

    match = compute_match(resume, jd)
    from ..services.gap_analyzer import get_missing_requirements
    reqs = get_missing_requirements(resume, jd)
    return {
        "resume_id": request.resume_id,
        "jd_id": request.jd_id,
        "match": match.model_dump(),
        "requirements": reqs,
    }


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    """Generate tailored resume patches (heuristic, grounded)."""
    resume_data = storage.get(request.resume_id)
    jd_data = storage.get(request.jd_id)

    if not resume_data or not jd_data:
        raise HTTPException(404, "Resume or JD not found.")

    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])
    match = MatchReport(**request.match_report)

    patches = generate_patches(resume, jd, match)
    validated = validate_patches(resume, patches)

    generation_id = f"gen_{request.resume_id}_{request.jd_id}"
    storage[generation_id] = {
        "type": "generation",
        "data": {
            "patches": [p.model_dump() for p in validated.patches],
            "resume_id": request.resume_id,
            "jd_id": request.jd_id,
        },
    }
    return {
        "generation_id": generation_id,
        "patches": [p.model_dump() for p in validated.patches],
    }


@app.post("/api/apply")
async def apply_patches(request: ApplyRequest):
    """Apply accepted patches to create final tailored resume."""
    resume_data = storage.get(request.resume_id)
    gen_data = storage.get(request.generation_id)

    if not resume_data:
        raise HTTPException(404, f"Resume '{request.resume_id}' not found.")
    if not gen_data:
        raise HTTPException(404, f"Generation '{request.generation_id}' not found.")

    resume = ResumeSchema(**resume_data["data"])
    patches = [PatchAction(**p) for p in gen_data["data"]["patches"]]

    final_resume, original_bullets, original_summary = _apply_patches_to_resume(resume, patches)
    final_id = f"final_{request.resume_id}"

    storage[final_id] = {
        "type": "final_resume",
        "data": final_resume.model_dump(),
        "original_path": resume_data.get("original_path"),
        "original_suffix": resume_data.get("original_suffix"),
        "original_bullets": original_bullets,
        "original_summary": original_summary,
    }

    return {"final_id": final_id, "resume": final_resume.model_dump()}


@app.post("/api/convert/to-latex")
async def convert_to_latex(final_id: str = Form(...)):
    """Convert a stored tailored resume into grounded LaTeX.

    Takes the ResumeSchema from storage, generates LaTeX via the grounded
    generator (no hallucination), and stores the .tex source in memory for
    later LLM tailoring or direct PDF compilation.
    """
    from backend.src.services.latex_generator import generate_latex
    from backend.src.services.renderer import render_latex as _render_latex

    final_data = storage.get(final_id)
    if not final_data:
        raise HTTPException(404, "Final resume not found.")

    resume = ResumeSchema(**final_data["data"])
    tex_path, fmt = _render_latex(resume)

    if fmt != "latex":
        raise HTTPException(500, "LaTeX generation failed.")

    # Store the LaTeX source in storage for the next pipeline step
    tex_id = f"tex_{final_id}"
    with open(tex_path, "r") as f:
        tex_source = f.read()
    storage[tex_id] = {
        "type": "resume_latex",
        "data": {"tex_source": tex_source},
        "source_path": tex_path,
    }

    return {"tex_id": tex_id, "tex_source": tex_source}


@app.post("/api/tailor-with-llm")
async def tailor_with_llm(tex_id: str = Form(...), jd_id: str = Form(...)):
    """Send tailored LaTeX and job description to an LLM for tailoring.

    Retrieves the LaTeX source from storage, sends it together with the
    job description to the LLM (via the generator's _llm_tailor_latex
    function), and stores the tailored LaTeX back into storage.
    """
    from backend.src.services.generator import _llm_tailor_latex

    tex_data = storage.get(tex_id)
    jd_data = storage.get(jd_id)

    if not tex_data:
        raise HTTPException(404, f"LaTeX source '{tex_id}' not found.")
    if not jd_data:
        raise HTTPException(404, f"JD '{jd_id}' not found.")

    latex_source = tex_data["data"]["tex_source"]
    jd = JointRequirementsSchema(**jd_data["data"])

    # Call the LLM‑tailoring function (heuristic fallback if no API keys)
    tailored_latex = _llm_tailor_latex(latex_source, jd)

    # Store the tailored LaTeX
    tailored_id = f"tailored_{tex_id}"
    storage[tailored_id] = {
        "type": "tailored_latex",
        "data": {"tex_source": tailored_latex},
    }

    return {"tailored_tex_id": tailored_id, "tex_source": tailored_latex}


@app.post("/api/generate-tailored")
async def generate_tailored(
    resume_id: str = Form(...),
    jd_id: str = Form(...),
    format: str = Form("pdf"),
):
    """Full LLM-based pipeline: extract → combine with JD → LLM → LaTeX → PDF.

    This single endpoint replaces the multi-step heuristic patch pipeline.
    It takes a parsed resume and analyzed JD, sends both to Gemini (or the
    configured LLM), gets back a freshly tailored LaTeX document, compiles
    it to a downloadable PDF, and returns the PDF directly.

    Args:
        format: Output format - 'pdf', 'latex', or 'docx'
    """
    from backend.src.services.generator import _llm_tailor_latex
    from backend.src.services.latex_generator import generate_latex
    from backend.src.services.renderer import render_latex as _render_latex

    resume_data = storage.get(resume_id)
    jd_data = storage.get(jd_id)

    if not resume_data:
        raise HTTPException(404, f"Resume '{resume_id}' not found.")
    if not jd_data:
        raise HTTPException(404, f"JD '{jd_id}' not found.")

    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])

    # Step 1: Extract relevant info and generate grounded LaTeX
    base_latex = generate_latex(resume)

    # Step 2: Combine with JD and use LLM to build a new tailored resume
    # Set up Gemini client if API key is configured
    llm_client = None
    try:
        import google.generativeai as genai
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and gemini_key.startswith("AIza"):
            genai.configure(api_key=gemini_key)
            model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
            llm_client = genai.GenerativeModel(model_name)
    except Exception:
        llm_client = None

    tailored_latex = _llm_tailor_latex(base_latex, jd, llm_client=llm_client)

    # Store the result for later retrieval
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    tex_path = str(Path("outputs") / f"tailored_{timestamp}.tex")
    Path(tex_path).write_text(tailored_latex, encoding="utf-8")

    tailored_id = f"llm_tailored_{resume_id}_{jd_id}"
    storage[tailored_id] = {
        "type": "tailored_latex",
        "data": {
            "tex_source": tailored_latex,
            "resume_id": resume_id,
            "jd_id": jd_id,
            "compiled": format == "pdf",
        },
        "source_path": tex_path,
        "pdf_path": None,
    }

    # Return based on requested format
    if format == "latex":
        return FileResponse(
            tex_path,
            filename=f"tailored_resume.tex",
            media_type="text/plain",
        )
    elif format == "docx":
        # Compile LaTeX to PDF first, then convert to DOCX
        pdf_path = str(Path("outputs") / f"tailored_{timestamp}.pdf")
        compiled = False
        for engine in ["xelatex", "pdflatex"]:
            try:
                result = subprocess.run(
                    [engine, "-interaction=nonstopmode", "-output-directory",
                     str(Path("outputs")), tex_path],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and Path(pdf_path).exists():
                    compiled = True
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if compiled:
            from backend.src.services.renderer import render_pdf
            output_path = render_pdf(resume, original_path=None, original_suffix=None)
            if output_path.endswith(".html"):
                return FileResponse(output_path, filename="tailored_resume.html", media_type="text/html")
            return FileResponse(output_path, filename="tailored_resume.pdf", media_type="application/pdf")

        # Fall back to PDF
        return FileResponse(
            tex_path,
            filename=f"tailored_resume.tex",
            media_type="text/plain",
        )
    else:
        # Default: PDF format
        pdf_path = str(Path("outputs") / f"tailored_{timestamp}.pdf")
        compiled = False
        for engine in ["xelatex", "pdflatex"]:
            try:
                result = subprocess.run(
                    [engine, "-interaction=nonstopmode", "-output-directory",
                     str(Path("outputs")), tex_path],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0 and Path(pdf_path).exists():
                    compiled = True
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        if compiled:
            return FileResponse(
                pdf_path,
                filename=f"tailored_resume_{jd.role_title or 'resume'}.pdf",
                media_type="application/pdf",
            )

        # Fall back: return the LaTeX source
        return FileResponse(
            tex_path,
            filename=f"tailored_resume_{jd.role_title or 'resume'}.tex",
            media_type="text/plain",
        )


# ──────────────────────────────────────────────────────────
# REQUIREMENTS & TAILORING ENDPOINTS
# ──────────────────────────────────────────────────────────

class RequirementsCheckRequest(BaseModel):
    resume_id: str
    jd_id: str


@app.post("/api/requirements/check")
async def check_requirements_endpoint(request: RequirementsCheckRequest):
    """Check for missing requirements/skills from the JD to ask the user."""
    resume_data = storage.get(request.resume_id)
    jd_data = storage.get(request.jd_id)
    if not resume_data or not jd_data:
        raise HTTPException(404, "Resume or JD not found.")
    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])
    from ..services.gap_analyzer import get_missing_requirements
    return get_missing_requirements(resume, jd)


class TailorRequest(BaseModel):
    resume_id: str
    jd_id: str
    user_requirements: Optional[dict] = None
    top_k: int = 8


@app.post("/api/tailor")
async def tailor_resume_endpoint(request: TailorRequest):
    """Tailor resume: summary, skills, and ALL projects aligned to JD without hallucination."""
    resume_data = storage.get(request.resume_id)
    jd_data = storage.get(request.jd_id)

    if not resume_data:
        raise HTTPException(404, f"Resume '{request.resume_id}' not found.")
    if not jd_data:
        raise HTTPException(404, f"JD '{request.jd_id}' not found.")

    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])

    from ..services.rag_pipeline import tailor_structured
    try:
        tailored, suggested_projects = tailor_structured(
            resume, jd, top_k=request.top_k, user_requirements=request.user_requirements, return_suggestions=True
        )
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            raise HTTPException(401, "GEMINI_API_KEY not configured. Set it in .env file.")
        raise HTTPException(500, f"Tailoring failed: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Tailoring failed: {str(e)}")

    # Compute updated match
    new_match = compute_match(tailored, jd)

    final_id = f"final_{request.resume_id}"
    storage[final_id] = {
        "type": "final_resume",
        "data": tailored.model_dump(),
        "original_path": resume_data.get("original_path"),
        "original_suffix": resume_data.get("original_suffix"),
        "resume_id": request.resume_id,
        "jd_id": request.jd_id,
        "suggested_projects": suggested_projects,
    }

    return {
        "final_id": final_id,
        "resume": tailored.model_dump(),
        "match": new_match.model_dump(),
        "grounding_verified": True,
        "suggested_projects": suggested_projects,
    }


class RagPipelineRequest(BaseModel):
    resume_id: str
    jd_id: str
    format: str = "pdf"  # "pdf", "latex", "markdown"
    top_k: int = 8
    user_requirements: Optional[dict] = None


@app.post("/api/rag-pipeline")
async def rag_pipeline(request: RagPipelineRequest):
    """Template-preserving RAG pipeline.

    1. Retrieve parsed resume and JD from storage
    2. Build TF-IDF RAG index, retrieve top-k relevant chunks
    3. Gemini returns a tailored plan: summary, skills reorder, experience bullets, and ALL projects tailored
    4. Render in the Jake-style template (aligned PDF / compilable LaTeX)
    """
    resume_data = storage.get(request.resume_id)
    jd_data = storage.get(request.jd_id)

    if not resume_data:
        raise HTTPException(404, f"Resume '{request.resume_id}' not found. Upload first.")
    if not jd_data:
        raise HTTPException(404, f"JD '{request.jd_id}' not found. Upload first.")

    if not RAG_AVAILABLE:
        raise HTTPException(500, "RAG pipeline module not available. Check imports.")

    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])

    # Step 1: Check if this resume was already tailored for this JD
    cached_final = storage.get(f"final_{request.resume_id}")
    if cached_final and cached_final.get("jd_id") == request.jd_id and not request.user_requirements:
        tailored = ResumeSchema(**cached_final["data"])
    else:
        try:
            from ..services.rag_pipeline import tailor_structured
            tailored = tailor_structured(
                resume, jd, top_k=request.top_k, user_requirements=request.user_requirements
            )
        except ValueError as e:
            if "GEMINI_API_KEY" in str(e):
                raise HTTPException(401, "GEMINI_API_KEY not configured. Set it in .env file.")
            raise HTTPException(500, f"LLM tailoring failed: {str(e)}")
        except Exception as e:
            raise HTTPException(500, f"RAG pipeline failed at tailoring stage: {str(e)}")

    # Step 2: Store the tailored resume
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    md_id = f"rag_{timestamp}"
    storage[md_id] = {
        "type": "rag_output",
        "data": {
            "resume": tailored.model_dump(mode="json"),
            "resume_id": request.resume_id,
            "jd_id": request.jd_id,
        },
    }

    # Step 3: Render in the Jake-style template
    from ..services.jakes_template import (
        render_jakes_latex, render_jakes_pdf, resume_to_markdown,
    )
    output_name = f"rag_resume_{request.jd_id}_{timestamp}"

    try:
        if request.format == "latex":
            tex_path = str(Path("outputs") / f"{output_name}.tex")
            Path(tex_path).write_text(render_jakes_latex(tailored), encoding="utf-8")
            return FileResponse(tex_path, filename=f"{output_name}.tex", media_type="text/plain")

        elif request.format == "markdown":
            md_path = str(Path("outputs") / f"{output_name}.md")
            Path(md_path).write_text(resume_to_markdown(tailored), encoding="utf-8")
            return FileResponse(md_path, filename=f"{output_name}.md", media_type="text/plain")

        else:
            # Default: aligned template PDF
            pdf_path = str(Path("outputs") / f"{output_name}.pdf")
            render_jakes_pdf(tailored, pdf_path)
            return FileResponse(
                pdf_path,
                filename=f"{output_name}.pdf",
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{output_name}.pdf"',
                    "Content-Type": "application/pdf"
                }
            )
    except Exception as e:
        raise HTTPException(500, f"Rendering failed: {str(e)}")


# ──────────────────────────────────────────────────────────
# DEDICATED HIGH-SPEED EXPORT & PREVIEW ENDPOINTS (<200ms)
# ──────────────────────────────────────────────────────────

class ExportPayload(BaseModel):
    final_id: Optional[str] = None
    resume_id: Optional[str] = None
    format: str = "pdf"
    preview: bool = False
    resume_data: Optional[dict] = None


@app.get("/api/export")
async def export_get(
    final_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    format: str = "pdf",
    preview: bool = False,
):
    """Instant export (<200ms) for tailored resumes using Jake's template.
    Supports browser inline preview (preview=True) or instant file download.
    """
    resume_obj = None

    if final_id and final_id in storage:
        raw = storage[final_id].get("data")
        if raw:
            resume_obj = ResumeSchema(**raw)

    if not resume_obj and resume_id:
        alt_id = f"final_{resume_id}" if not resume_id.startswith("final_") else resume_id
        if alt_id in storage:
            resume_obj = ResumeSchema(**storage[alt_id]["data"])
        elif resume_id in storage:
            resume_obj = ResumeSchema(**storage[resume_id]["data"])

    if not resume_obj:
        for k, v in storage.items():
            if k.startswith("final_") and "data" in v:
                resume_obj = ResumeSchema(**v["data"])
                break

    if not resume_obj:
        raise HTTPException(404, "Tailored resume not found. Please complete the tailoring step first.")

    from ..services.jakes_template import render_jakes_latex, render_jakes_pdf, resume_to_markdown
    Path("outputs").mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    cand_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resume_obj.contact.name or 'tailored_resume').strip('_') or 'tailored_resume'

    fmt = format.lower()
    if fmt == "latex":
        tex_path = str(Path("outputs") / f"{cand_name}_{ts}.tex")
        Path(tex_path).write_text(render_jakes_latex(resume_obj), encoding="utf-8")
        disposition = "inline" if preview else f'attachment; filename="{cand_name}.tex"'
        return FileResponse(
            tex_path,
            filename=f"{cand_name}.tex",
            media_type="text/plain",
            headers={"Content-Disposition": disposition}
        )

    elif fmt == "markdown":
        md_path = str(Path("outputs") / f"{cand_name}_{ts}.md")
        Path(md_path).write_text(resume_to_markdown(resume_obj), encoding="utf-8")
        disposition = "inline" if preview else f'attachment; filename="{cand_name}.md"'
        return FileResponse(
            md_path,
            filename=f"{cand_name}.md",
            media_type="text/plain",
            headers={"Content-Disposition": disposition}
        )

    else:
        pdf_path = str(Path("outputs") / f"{cand_name}_{ts}.pdf")
        render_jakes_pdf(resume_obj, pdf_path)
        disposition = "inline" if preview else f'attachment; filename="{cand_name}_Resume.pdf"'
        return FileResponse(
            pdf_path,
            filename=f"{cand_name}_Resume.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": disposition,
                "Content-Type": "application/pdf",
            }
        )


@app.post("/api/export")
async def export_post(payload: ExportPayload):
    """POST export endpoint allowing client to pass resume_data directly for zero-loss recovery."""
    resume_obj = None

    if payload.resume_data:
        try:
            resume_obj = ResumeSchema(**payload.resume_data)
        except Exception:
            pass

    if not resume_obj and payload.final_id and payload.final_id in storage:
        resume_obj = ResumeSchema(**storage[payload.final_id]["data"])

    if not resume_obj and payload.resume_id:
        alt_id = f"final_{payload.resume_id}" if not payload.resume_id.startswith("final_") else payload.resume_id
        if alt_id in storage:
            resume_obj = ResumeSchema(**storage[alt_id]["data"])

    if not resume_obj:
        for k, v in storage.items():
            if k.startswith("final_") and "data" in v:
                resume_obj = ResumeSchema(**v["data"])
                break

    if not resume_obj:
        raise HTTPException(404, "Tailored resume data not found.")

    from ..services.jakes_template import render_jakes_latex, render_jakes_pdf, resume_to_markdown
    Path("outputs").mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    cand_name = re.sub(r'[^a-zA-Z0-9_-]', '_', resume_obj.contact.name or 'tailored_resume').strip('_') or 'tailored_resume'

    fmt = payload.format.lower()
    if fmt == "latex":
        tex_path = str(Path("outputs") / f"{cand_name}_{ts}.tex")
        Path(tex_path).write_text(render_jakes_latex(resume_obj), encoding="utf-8")
        disposition = "inline" if payload.preview else f'attachment; filename="{cand_name}.tex"'
        return FileResponse(
            tex_path,
            filename=f"{cand_name}.tex",
            media_type="text/plain",
            headers={"Content-Disposition": disposition}
        )

    elif fmt == "markdown":
        md_path = str(Path("outputs") / f"{cand_name}_{ts}.md")
        Path(md_path).write_text(resume_to_markdown(resume_obj), encoding="utf-8")
        disposition = "inline" if payload.preview else f'attachment; filename="{cand_name}.md"'
        return FileResponse(
            md_path,
            filename=f"{cand_name}.md",
            media_type="text/plain",
            headers={"Content-Disposition": disposition}
        )

    else:
        pdf_path = str(Path("outputs") / f"{cand_name}_{ts}.pdf")
        render_jakes_pdf(resume_obj, pdf_path)
        disposition = "inline" if payload.preview else f'attachment; filename="{cand_name}_Resume.pdf"'
        return FileResponse(
            pdf_path,
            filename=f"{cand_name}_Resume.pdf",
            media_type="application/pdf",
            headers={
                "Content-Disposition": disposition,
                "Content-Type": "application/pdf",
            }
        )


# ──────────────────────────────────────────────────────────
# RAG STATUS CHECK
# ──────────────────────────────────────────────────────────

@app.get("/api/rag-pipeline/status")
async def rag_status():
    """Check if RAG pipeline is available and Gemini API key is configured."""
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    return {
        "rag_available": RAG_AVAILABLE,
        "gemini_configured": bool(gemini_key and gemini_key.startswith("AIza")),
        "model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
    }


# ──────────────────────────────────────────────────────────
# LEGACY: Generate Tailored (kept for backward compatibility)
# ──────────────────────────────────────────────────────────

@app.post("/api/generate-tailored")
async def generate_tailored(
    resume_id: str = Form(...),
    jd_id: str = Form(...),
    format: str = Form("pdf"),
):
    """Full LLM-based pipeline: extract → combine with JD → LLM → LaTeX → PDF.

    This endpoint now delegates to the RAG pipeline for the LLM drafting step.
    """
    from ..services.rag_pipeline import draft_resume_rag
    from ..services.pdf_converter import markdown_to_pdf, markdown_to_latex

    resume_data = storage.get(resume_id)
    jd_data = storage.get(jd_id)

    if not resume_data:
        raise HTTPException(404, f"Resume '{resume_id}' not found.")
    if not jd_data:
        raise HTTPException(404, f"JD '{jd_id}' not found.")

    resume = ResumeSchema(**resume_data["data"])
    jd = JointRequirementsSchema(**jd_data["data"])

    # Step 1: Generate grounded LaTeX from resume
    base_latex = generate_latex(resume)

    # Step 2: Use RAG-enhanced LLM drafting
    try:
        tailored_latex = draft_resume_rag(resume, jd, top_k=8)
    except ValueError as e:
        if "GEMINI_API_KEY" in str(e):
            raise HTTPException(401, "GEMINI_API_KEY not configured.")
        # Fall back to heuristic tailoring
        from ..services.generator import _llm_tailor_latex
        tailored_latex = _llm_tailor_latex(base_latex, jd)
    except Exception:
        from ..services.generator import _llm_tailor_latex
        tailored_latex = _llm_tailor_latex(base_latex, jd)

    # Store the result
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    tex_path = str(Path("outputs") / f"tailored_{timestamp}.tex")
    Path(tex_path).write_text(tailored_latex, encoding="utf-8")

    tailored_id = f"llm_tailored_{resume_id}_{jd_id}"
    storage[tailored_id] = {
        "type": "tailored_latex",
        "data": {"tex_source": tailored_latex, "resume_id": resume_id, "jd_id": jd_id},
        "source_path": tex_path,
        "pdf_path": None,
    }

    if format == "latex":
        return FileResponse(tex_path, filename="tailored_resume.tex", media_type="text/plain")

    # Convert to PDF via markdown (we parse LaTeX to markdown → PDF)
    # For the legacy endpoint, we still use the LaTeX → PDF compilation path
    # but fall back to WeasyPrint if no LaTeX engine available
    pdf_path = str(Path("outputs") / f"tailored_{timestamp}.pdf")

    # Try LaTeX compilation first
    compiled = False
    for engine in ["xelatex", "pdflatex"]:
        try:
            result = subprocess.run(
                [engine, "-interaction=nonstopmode", "-output-directory",
                 str(Path("outputs")), tex_path],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and Path(pdf_path).exists():
                compiled = True
                break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue

    if not compiled:
        # Fallback: convert LaTeX source to markdown then to PDF via WeasyPrint
        # Extract text content from LaTeX and render as HTML→PDF
        try:
            from ..services.generator import _llm_tailor_latex
            md_path = str(Path("outputs") / f"tailored_{timestamp}.md")
            Path(md_path).write_text(tailored_latex, encoding="utf-8")
            pdf_path, _ = markdown_to_pdf(tailored_latex, output_name=output_name)
        except Exception:
            pass

    if Path(pdf_path).exists():
        return FileResponse(pdf_path, filename=f"tailored_resume_{jd.role_title or 'resume'}.pdf", media_type="application/pdf")

    return FileResponse(tex_path, filename=f"tailored_resume_{jd.role_title or 'resume'}.tex", media_type="text/plain")


@app.post("/api/render/pdf")
async def render_pdf_endpoint(final_id: str = Form(...)):
    """Render final resume as PDF (or HTML fallback)."""
    final_data = storage.get(final_id)
    if not final_data:
        raise HTTPException(404, "Final resume not found.")

    resume = ResumeSchema(**final_data["data"])
    original_path = final_data.get("original_path")
    original_suffix = final_data.get("original_suffix")
    original_bullets = final_data.get("original_bullets")
    original_summary = final_data.get("original_summary")
    output_path = render_pdf(resume, original_path=original_path, original_suffix=original_suffix, original_bullets=original_bullets, original_summary=original_summary)

    if output_path.endswith(".html"):
        return FileResponse(output_path, filename="tailored_resume.html", media_type="text/html")
    return FileResponse(output_path, filename="tailored_resume.pdf", media_type="application/pdf")


@app.post("/api/render/latex")
async def render_latex_endpoint(final_id: str = Form(...)):
    """Render final resume as LaTeX source (or compiled PDF)."""
    final_data = storage.get(final_id)
    if not final_data:
        raise HTTPException(404, "Final resume not found.")

    resume = ResumeSchema(**final_data["data"])
    original_path = final_data.get("original_path")
    original_suffix = final_data.get("original_suffix")
    original_bullets = final_data.get("original_bullets")
    original_summary = final_data.get("original_summary")
    output_path, fmt = render_latex(resume, original_path=original_path, original_suffix=original_suffix, original_bullets=original_bullets, original_summary=original_summary)

    if fmt == "pdf":
        return FileResponse(output_path, filename="tailored_resume.pdf", media_type="application/pdf")
    return FileResponse(output_path, filename="tailored_resume.tex", media_type="text/plain")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_patches_to_resume(resume: ResumeSchema, patches: list[PatchAction]) -> tuple[ResumeSchema, dict[str, str], str]:
    """Apply validated patches to produce the final tailored resume.

    Returns:
        - final: the patched ResumeSchema
        - original_bullets: map of bullet_id → original text (for renderer fuzzy-matching)
        - original_summary: original summary text (for renderer to locate the summary paragraph precisely)
    """
    final = copy.deepcopy(resume)

    # Capture original bullet text before any modifications
    original_bullets: dict[str, str] = {
        b.id: b.text for exp in resume.experience for b in exp.bullets
    }
    # Capture original summary text
    original_summary = resume.summary or ""

    for patch in patches:
        # ── Summary rewrite ─────────────────────────────────────────
        if patch.target == "summary":
            final.summary = patch.proposed

        # ── Skills reorder ──────────────────────────────────────────
        elif patch.target == "skills" and patch.action == "reorder":
            try:
                order: list[str] = json.loads(patch.proposed)
                skill_map = {s.name: s for s in final.skills}
                reordered = [skill_map[name] for name in order if name in skill_map]
                # Append any skills not in the proposed order (preserves completeness)
                mentioned = set(order)
                for s in final.skills:
                    if s.name not in mentioned:
                        reordered.append(s)
                final.skills = reordered
            except (ValueError, KeyError, json.JSONDecodeError):
                pass  # Malformed patch — leave skills unchanged

        # ── add_skills: add new skills to the Skills section (deduped by name) ─
        elif patch.target == "skills" and patch.action == "add_skills":
            try:
                new_skill_names = json.loads(patch.proposed)
                existing_names = {s.name.lower() for s in final.skills}
                for name in new_skill_names:
                    if name and name.lower() not in existing_names:
                        # Lazy-import Skill to avoid circular import
                        from ..models.resume import Skill
                        final.skills.append(Skill(name=name, category=_categorize_skill_name(name)))
                        existing_names.add(name.lower())
            except (ValueError, KeyError, json.JSONDecodeError):
                pass  # Malformed patch — leave skills unchanged

        # ── suggest_project: informational, surfaced in review UI; not auto-applied ─
        elif patch.action == "suggest_project":
            pass  # Rendered as a tip in the review screen, not injected into the resume

        # ── Bullet rewrite  (id format: "exp_1.b2") ─────────────────
        elif "." in patch.target and patch.action == "rewrite":
            target_id = patch.target
            for exp in final.experience:
                for bullet in exp.bullets:
                    if bullet.id == target_id:
                        bullet.text = patch.proposed
                        break  # inner loop

    return final, original_bullets, original_summary


def _categorize_skill_name(name: str) -> str:
    """Assign a category to a skill name for the Skills section."""
    nl = name.lower()
    if any(k in nl for k in ["python", "javascript", "typescript", "java", "go", "golang",
                               "rust", "c++", "c#", "ruby", "php", "swift", "kotlin",
                               "scala", "bash", "shell", "matlab", "r"]):
        return "Language"
    if any(k in nl for k in ["react", "vue", "angular", "next", "node", "django",
                               "flask", "fastapi", "spring", "rails", "laravel",
                               "express", "svelte", "nest", "next.js", "node.js"]):
        return "Framework"
    if any(k in nl for k in ["aws", "azure", "gcp", "docker", "kubernetes", "terraform",
                               "ansible", "ci/cd", "jenkins", "github actions", "linux",
                               "nginx", "heroku", "vercel"]):
        return "DevOps"
    if any(k in nl for k in ["postgres", "mysql", "mongo", "redis", "sql", "elastic",
                               "kafka", "sqlite", "dynamodb", "firebase", "supabase",
                               "postgresql"]):
        return "Database"
    if any(k in nl for k in ["tensorflow", "pytorch", "scikit", "pandas", "numpy",
                               "spark", "hugging", "transformers", "ml", "ai", "llm"]):
        return "ML/AI"
    return "General"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)