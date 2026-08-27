"""FastAPI application with all pipeline endpoints."""
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
from ..services.generator import generate_patches, PatchList
from ..services.validator import validate_patches
from ..services.renderer import render_docx, render_pdf
from ..models.resume import ResumeSchema, JointRequirementsSchema, PatchAction


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
    """Upload and parse resume file (PDF/DOCX). Original file is preserved for template rendering."""
    content = await file.read()
    suffix = Path(file.filename).suffix.lower()

    if suffix not in (".pdf", ".docx", ".doc"):
        raise HTTPException(400, "Unsupported file format. Use PDF or DOCX.")

    # Save the original file permanently so the renderer can use it as a template
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
        "original_path": str(original_path),  # kept for template-preserving render
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
    return {
        "resume_id": request.resume_id,
        "jd_id": request.jd_id,
        "match": match.model_dump(),
    }


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    """Generate tailored resume patches."""
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
    """Apply accepted patches to create final tailored resume (JSON body)."""
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

    # Store original path, bullets, and summary so renderer can do template-preserving in-place patch
    storage[final_id] = {
        "type": "final_resume",
        "data": final_resume.model_dump(),
        "original_path": resume_data.get("original_path"),
        "original_suffix": resume_data.get("original_suffix"),
        "original_bullets": original_bullets,
        "original_summary": original_summary,
    }

    return {"final_id": final_id, "resume": final_resume.model_dump()}


@app.post("/api/render/docx")
async def render_docx_endpoint(final_id: str = Form(...)):
    """Render final resume as DOCX."""
    final_data = storage.get(final_id)
    if not final_data:
        raise HTTPException(404, "Final resume not found.")

    resume = ResumeSchema(**final_data["data"])
    original_path = final_data.get("original_path")
    original_suffix = final_data.get("original_suffix")
    original_bullets = final_data.get("original_bullets")
    original_summary = final_data.get("original_summary")
    output_path = render_docx(resume, original_path=original_path, original_suffix=original_suffix, original_bullets=original_bullets, original_summary=original_summary)
    return FileResponse(
        output_path,
        filename="tailored_resume.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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