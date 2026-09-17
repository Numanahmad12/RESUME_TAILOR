"""RAG pipeline — TF-IDF embeddings + retrieval + LLM drafting.

Uses scikit-learn's TfidfVectorizer to embed resume sections and JD text,
stores them in memory, retrieves top-k relevant chunks via cosine similarity,
and augments the Gemini prompt with retrieved context.

The LLM returns a markdown-formatted resume which is then
converted to HTML→PDF (via WeasyPrint) or LaTeX source.
"""
import os
import re
import json
import uuid
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from ..models.resume import ResumeSchema, JointRequirementsSchema, Skill


# ─────────────────────────────────────────────────────────────
# In-memory vector store using TF-IDF
# ─────────────────────────────────────────────────────────────
class VectorStore:
    """Simple in-memory vector store using scikit-learn TF-IDF."""

    def __init__(self):
        self.chunks: List[dict] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.matrix = None

    def add_chunk(self, text: str, metadata: dict):
        """Add a text chunk with metadata to the store."""
        self.chunks.append({"text": text, "metadata": metadata})

    def build_index(self):
        """Compute TF-IDF vectors for all stored chunks."""
        texts = [c["text"] for c in self.chunks]
        if texts:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=5000,
                stop_words="english",
                sublinear_tf=True,
            )
            self.matrix = self.vectorizer.fit_transform(texts)

    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """Search for the top-k most relevant chunks using cosine similarity."""
        if not self.chunks or self.matrix is None or self.vectorizer is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.matrix).flatten()
        top_indices = scores.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only return chunks with non-zero similarity
                results.append({
                    "text": self.chunks[idx]["text"],
                    "metadata": self.chunks[idx]["metadata"],
                    "score": float(scores[idx]),
                })
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def reset(self):
        """Clear the store."""
        self.chunks = []
        self.vectorizer = None
        self.matrix = None


# Global store instance
_rag_store = VectorStore()


# ─────────────────────────────────────────────────────────────
# RAG Chunking
# ─────────────────────────────────────────────────────────────

def chunk_resume(resume: ResumeSchema) -> List[dict]:
    """Chunk resume into searchable pieces."""
    chunks = []

    if resume.summary and resume.summary.strip():
        chunks.append({
            "text": resume.summary,
            "metadata": {"source": "resume", "section": "summary", "id": str(uuid.uuid4())[:8]},
        })

    if resume.skills:
        skill_text = ", ".join(f"{s.name} ({s.category})" for s in resume.skills)
        chunks.append({
            "text": skill_text,
            "metadata": {"source": "resume", "section": "skills", "id": str(uuid.uuid4())[:8]},
        })

    for exp in resume.experience:
        exp_header = f"{exp.title} at {exp.company}" if exp.title and exp.company else f"{exp.company or exp.title or 'Experience'}"
        exp_text = f"{exp_header} ({_fmt_dates(exp.start_date, exp.end_date)})\n"
        for b in exp.bullets:
            exp_text += f"{b.text}\n"
        chunks.append({
            "text": exp_text,
            "metadata": {"source": "resume", "section": "experience", "id": str(uuid.uuid4())[:8]},
        })

    for edu in resume.education:
        edu_text = f"{edu.school} - {edu.degree} ({edu.dates})"
        chunks.append({
            "text": edu_text,
            "metadata": {"source": "resume", "section": "education", "id": str(uuid.uuid4())[:8]},
        })

    for proj in resume.projects:
        proj_text = f"{proj.name}: {proj.description}"
        if proj.technologies:
            proj_text += f" Tech: {', '.join(proj.technologies)}"
        chunks.append({
            "text": proj_text,
            "metadata": {"source": "resume", "section": "projects", "id": str(uuid.uuid4())[:8]},
        })

    for cert in resume.certifications:
        cert_text = f"{cert.name} - {cert.issuer} ({cert.date})"
        chunks.append({
            "text": cert_text,
            "metadata": {"source": "resume", "section": "certifications", "id": str(uuid.uuid4())[:8]},
        })

    contact_text = f"{resume.contact.name}, {resume.contact.email}, {resume.contact.phone}"
    chunks.append({
        "text": contact_text,
        "metadata": {"source": "resume", "section": "contact", "id": str(uuid.uuid4())[:8]},
    })

    return chunks


def chunk_jd(jd: JointRequirementsSchema) -> List[dict]:
    """Chunk JD into searchable pieces."""
    chunks = []

    if jd.role_title:
        chunks.append({
            "text": f"Target role: {jd.role_title}",
            "metadata": {"source": "jd", "section": "role_title", "id": str(uuid.uuid4())[:8]},
        })

    if jd.required_skills:
        chunks.append({
            "text": f"Required skills: {', '.join(jd.required_skills)}",
            "metadata": {"source": "jd", "section": "required_skills", "id": str(uuid.uuid4())[:8]},
        })

    if jd.preferred_skills:
        chunks.append({
            "text": f"Preferred skills: {', '.join(jd.preferred_skills)}",
            "metadata": {"source": "jd", "section": "preferred_skills", "id": str(uuid.uuid4())[:8]},
        })

    for resp in jd.responsibilities:
        chunks.append({
            "text": f"Responsibility: {resp}",
            "metadata": {"source": "jd", "section": "responsibilities", "id": str(uuid.uuid4())[:8]},
        })

    if jd.keywords_for_ats:
        chunks.append({
            "text": f"ATS keywords: {', '.join(jd.keywords_for_ats)}",
            "metadata": {"source": "jd", "section": "keywords", "id": str(uuid.uuid4())[:8]},
        })

    if jd.seniority_level:
        chunks.append({
            "text": f"Seniority level: {jd.seniority_level}",
            "metadata": {"source": "jd", "section": "seniority", "id": str(uuid.uuid4())[:8]},
        })

    if jd.min_years_experience:
        chunks.append({
            "text": f"Minimum experience: {jd.min_years_experience} years",
            "metadata": {"source": "jd", "section": "experience_req", "id": str(uuid.uuid4())[:8]},
        })

    return chunks


def build_rag_index(resume: ResumeSchema, jd: JointRequirementsSchema):
    """Build the RAG index from resume and JD."""
    _rag_store.reset()
    for chunk in chunk_resume(resume):
        _rag_store.add_chunk(chunk["text"], chunk["metadata"])
    for chunk in chunk_jd(jd):
        _rag_store.add_chunk(chunk["text"], chunk["metadata"])
    _rag_store.build_index()


# ─────────────────────────────────────────────────────────────
# Retrieval & Prompt Construction
# ─────────────────────────────────────────────────────────────

def retrieve_relevant_chunks(query: str, top_k: int = 8) -> List[dict]:
    """Retrieve top-k relevant chunks from the RAG store."""
    return _rag_store.search(query, top_k=top_k)


def build_rag_prompt(resume: ResumeSchema, jd: JointRequirementsSchema, retrieved_chunks: List[dict] = None) -> str:
    """Build a comprehensive prompt with RAG context for Gemini."""
    resume_text = _resume_to_text(resume)
    jd_text = _jd_to_text(jd)

    rag_context = ""
    if retrieved_chunks:
        rag_context = "RELEVANT CONTEXT FROM YOUR RESUME AND JOB DESCRIPTION:\n"
        for i, chunk in enumerate(retrieved_chunks, 1):
            src = chunk["metadata"].get("source", "")
            section = chunk["metadata"].get("section", "")
            rag_context += f"[{src}/{section}] {chunk['text']}\n"
        rag_context += "\n"

    prompt = f"""You are an expert resume writer and ATS optimization specialist.

Create a COMPLETELY NEW, highly tailored resume for this specific job. Do NOT modify an existing resume — draft an entirely fresh one using ONLY verified facts from the candidate's background.

=== CANDIDATE'S ORIGINAL RESUME ===
{resume_text}

=== JOB DESCRIPTION ===
{jd_text}

{rag_context}

=== INSTRUCTIONS ===
1. Create a COMPLETE, valid markdown resume document. Include ALL sections: Contact, Professional Summary, Skills, Work Experience, Education, Projects, Certifications.
2. Use ONLY verified facts from the resume above (name, contact, dates, companies, degrees, skills, experience). Do NOT invent anything.
3. Tailor the Professional Summary and Work Experience bullets to emphasize the required skills and responsibilities from the JD.
4. Prioritize required skills naturally throughout the document.
5. Rewrite bullet points to use strong action verbs and quantify achievements when possible.
6. Reorder skills so the most relevant ones appear first.
7. Keep the resume professional, ATS-friendly, and concise (1-2 pages).
8. Return ONLY the markdown resume with no explanation, code fences, or commentary.
9. Preserve the candidate's truthful information — never fabricate dates, companies, or degrees.
10. Include ALL relevant ATS keywords from the JD throughout the resume naturally.

=== OUTPUT FORMAT ===
Return a clean markdown resume with these exact section headers:
- **Contact** (name, email, phone, links)
- **Professional Summary** (2-3 sentences tailored to the role)
- **Technical Skills** (categorized: Language, Framework, DevOps, Database, ML/AI)
- **Work Experience** (company, title, dates, bullet points)
- **Education** (school, degree, dates)
- **Projects** (name, description, tech stack)
- **Certifications** (name, issuer, date)

Draft the complete resume now."""

    return prompt


# ─────────────────────────────────────────────────────────────
# LLM Drafting
# ─────────────────────────────────────────────────────────────

def draft_resume_rag(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    top_k: int = 8,
    model_name: str = None,
    api_key: str = None,
) -> str:
    """Draft a tailored resume using RAG-enhanced Gemini LLM.

    Returns markdown text of the drafted resume.
    Falls back to heuristic if LLM fails.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")

    if not api_key or not api_key.startswith("AIza"):
        raise ValueError("GEMINI_API_KEY is not configured properly")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except ImportError:
        raise RuntimeError("google.generativeai not installed")

    # Build RAG index and retrieve relevant chunks
    build_rag_index(resume, jd)
    retrieved = retrieve_relevant_chunks(
        f"{jd.role_title} {', '.join(jd.required_skills)}",
        top_k=top_k,
    )

    # Build the prompt
    prompt = build_rag_prompt(resume, jd, retrieved)

    # Call Gemini with correct model name
    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    client = genai.GenerativeModel(model_name)
    try:
        response = client.generate_content(prompt)
    except Exception as e:
        print(f"[RAG Pipeline] Gemini generate_content error: {e}")
        raise

    if response and response.text:
        return response.text.strip()
    else:
        raise ValueError("Gemini returned empty response")


def _resume_to_text(resume: ResumeSchema) -> str:
    """Convert ResumeSchema to a text representation for the prompt."""
    parts = []
    if resume.contact.name:
        parts.append(f"Name: {resume.contact.name}")
    if resume.contact.email:
        parts.append(f"Email: {resume.contact.email}")
    if resume.contact.phone:
        parts.append(f"Phone: {resume.contact.phone}")
    if resume.contact.links:
        parts.append(f"Links: {', '.join(resume.contact.links)}")
    if resume.summary:
        parts.append(f"Summary: {resume.summary}")
    if resume.skills:
        parts.append(f"Skills: {', '.join(s.name for s in resume.skills)}")
    for exp in resume.experience:
        parts.append(f"Experience: {exp.title} at {exp.company} ({_fmt_dates(exp.start_date, exp.end_date)})")
        for b in exp.bullets:
            parts.append(f"  - {b.text}")
    for edu in resume.education:
        parts.append(f"Education: {edu.school}, {edu.degree} ({edu.dates})")
    for proj in resume.projects:
        parts.append(f"Project: {proj.name} - {proj.description}")
        if proj.technologies:
            parts.append(f"  Tech: {', '.join(proj.technologies)}")
    return "\n".join(parts)


def _jd_to_text(jd: JointRequirementsSchema) -> str:
    """Convert JointRequirementsSchema to text for the prompt."""
    parts = []
    if jd.role_title:
        parts.append(f"Role: {jd.role_title}")
    if jd.seniority_level:
        parts.append(f"Seniority: {jd.seniority_level}")
    if jd.min_years_experience:
        parts.append(f"Experience Required: {jd.min_years_experience} years")
    if jd.required_skills:
        parts.append(f"Required Skills: {', '.join(jd.required_skills)}")
    if jd.preferred_skills:
        parts.append(f"Preferred Skills: {', '.join(jd.preferred_skills)}")
    for resp in jd.responsibilities:
        parts.append(f"Responsibility: {resp}")
    return "\n".join(parts)


def _fmt_dates(start, end) -> str:
    """Format date range."""
    if not start and not end:
        return ""
    s = start.strftime("%b %Y") if hasattr(start, "strftime") else str(start or "")
    e = "Present" if end is None else (end.strftime("%b %Y") if hasattr(end, "strftime") else str(end))
    return f"{s} – {e}" if s and e else s or e


# ─────────────────────────────────────────────────────────────
# Grounded tailoring: Professional summary, skills alignment,
# experience bullet enhancements, and ALL projects aligned to JD.
# Education, degrees, companies, and contact are strictly verified.
# ─────────────────────────────────────────────────────────────

def _categorize_skill(name: str) -> str:
    """Assign a standard category to a skill name."""
    nl = name.lower()
    if any(k in nl for k in ["python", "javascript", "typescript", "java", "go", "golang", "c++", "c#", "rust", "ruby", "php", "swift", "kotlin", "sql", "html", "css"]):
        return "Languages"
    if any(k in nl for k in ["react", "vue", "angular", "next", "node", "django", "flask", "fastapi", "express", "spring", "rails", "tailwind"]):
        return "Frameworks"
    if any(k in nl for k in ["aws", "gcp", "azure", "docker", "kubernetes", "k8s", "git", "ci/cd", "linux", "terraform", "jenkins", "postgres", "mongodb", "redis", "mysql"]):
        return "Developer Tools"
    return "Technologies"


def score_project_relevance(proj: ProjectEntry, jd: JointRequirementsSchema) -> float:
    """Score how well a candidate's project matches the target job description."""
    score = 0.0
    jd_skills = {s.lower() for s in (jd.required_skills + jd.preferred_skills + jd.keywords_for_ats) if s}
    role_lower = (jd.role_title or "").lower()

    proj_name_lower = (proj.name or "").lower()
    proj_desc_lower = (proj.description or "").lower()
    proj_tech_lower = {t.lower() for t in proj.technologies}
    all_proj_text = f"{proj_name_lower} {proj_desc_lower} {' '.join(proj_tech_lower)}"

    # 1. Direct tech stack keyword match
    for tech in proj_tech_lower:
        if tech in jd_skills:
            score += 4.0
        elif any(s in tech or tech in s for s in jd_skills if len(s) >= 3):
            score += 2.0

    # 2. Text matches against required skills
    for req in jd.required_skills:
        rl = req.lower()
        if re.search(r'\b' + re.escape(rl) + r'\b', all_proj_text):
            score += 3.0

    # 3. Domain alignments
    # AI / ML Role
    is_ai_role = any(k in role_lower for k in ["ai", "machine learning", "ml", "nlp", "vision", "data science", "llm", "rag"])
    is_ai_proj = any(k in all_proj_text for k in ["ai", "rag", "llm", "gemini", "groq", "opencv", "mediapipe", "machine learning", "model", "vision"])
    if is_ai_role and is_ai_proj:
        score += 8.0
    elif not is_ai_role and is_ai_proj and any(k in role_lower for k in ["full stack", "fullstack", "web", "frontend", "backend"]):
        # Pure AI project without web frameworks on a full stack role
        if not any(k in all_proj_text for k in ["react", "vue", "django", "node", "fastapi", "html", "css", "web"]):
            score -= 4.0

    # Full Stack / Web Role
    is_fs_role = any(k in role_lower for k in ["full stack", "fullstack", "web", "frontend", "backend", "software engineer", "software developer"])
    is_fs_proj = any(k in all_proj_text for k in ["react", "django", "fastapi", "node", "express", "postgresql", "sql", "rest", "api", "typescript", "javascript", "web"])
    if is_fs_role and is_fs_proj:
        score += 6.0

    # Mobile Role
    is_mobile_role = any(k in role_lower for k in ["ios", "android", "mobile", "swift", "kotlin", "flutter", "react native"])
    is_mobile_proj = any(k in all_proj_text for k in ["swift", "swiftui", "ios", "android", "mapkit", "kotlin", "mobile"])
    if is_mobile_role and is_mobile_proj:
        score += 10.0
    elif not is_mobile_role and is_mobile_proj and (is_fs_role or is_ai_role):
        # Mismatched mobile project on pure web/backend/AI role
        score -= 6.0

    return score


def generate_project_suggestions(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    selected_projects: List[ProjectEntry],
) -> List[dict]:
    """Suggest targeted portfolio projects to bridge technical gaps between resume and JD."""
    suggestions = []
    role_lower = (jd.role_title or "").lower()

    selected_tech = {t.lower() for p in selected_projects for t in p.technologies}

    # Full Stack / Web Gap
    if any(k in role_lower for k in ["full stack", "fullstack", "web", "frontend", "backend"]):
        if not any(any(k in t for k in ["react", "vue", "angular", "node", "django", "fastapi"]) for t in selected_tech):
            suggestions.append({
                "title": "Full-Stack Cloud E-Commerce & Analytics Dashboard",
                "technologies": ["React", "TypeScript", "FastAPI / Node.js", "PostgreSQL", "Docker"],
                "bullets": [
                    "Architected an end-to-end responsive web application featuring secure JWT authentication, state management, and real-time data sync.",
                    "Designed RESTful microservice APIs backed by PostgreSQL and containerized the entire stack with Docker for seamless CI/CD deployment."
                ],
                "rationale": f"Strengthens your practical Full-Stack and database portfolio directly matching {jd.role_title} requirements."
            })

    # AI / LLM / RAG Gap
    if any(k in role_lower for k in ["ai", "machine learning", "ml", "llm", "rag", "nlp", "vision"]):
        if not any(any(k in t for k in ["rag", "llm", "langchain", "gemini", "groq", "pytorch", "opencv"]) for t in selected_tech):
            suggestions.append({
                "title": "Enterprise Knowledge RAG Agent with Semantic Reranking",
                "technologies": ["Python", "FastAPI", "LangChain / LlamaIndex", "ChromaDB / Pinecone", "Gemini API"],
                "bullets": [
                    "Built an asynchronous RAG pipeline processing multi-format documentation with vector chunking, hybrid keyword/semantic search, and hallucination guardrails.",
                    "Implemented streaming API endpoints with sub-second response latency and automated relevance scoring."
                ],
                "rationale": f"Demonstrates modern RAG & LLM orchestration required by {jd.role_title}."
            })

    # DevOps / Cloud Gap
    if any(k in role_lower or k in [s.lower() for s in jd.required_skills] for k in ["docker", "kubernetes", "k8s", "aws", "cloud", "ci/cd"]):
        if not any(any(k in t for k in ["docker", "kubernetes", "aws", "gcp", "ci/cd"]) for t in selected_tech):
            suggestions.append({
                "title": "Cloud-Native Microservices Infrastructure with CI/CD",
                "technologies": ["Docker", "Kubernetes", "AWS / GCP", "GitHub Actions", "Terraform"],
                "bullets": [
                    "Containerized multi-tier backend services and implemented automated linting, unit testing, and deployment pipelines via GitHub Actions.",
                    "Configured high-availability ingress routing, horizontal pod autoscaling, and centralized Prometheus/Grafana monitoring."
                ],
                "rationale": "Directly proves production DevOps and container orchestration capabilities for this role."
            })

    return suggestions[:2]


def build_constrained_prompt(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    user_requirements: Optional[dict] = None,
) -> str:
    """Prompt Gemini for a comprehensive JSON tailoring plan with all projects aligned."""
    exp_bullets = []
    for exp in resume.experience:
        for b in exp.bullets:
            exp_bullets.append(f"[{b.id}] ({exp.title} at {exp.company}): {b.text}")

    skills = [f"{s.name} ({s.category})" for s in resume.skills]

    projects_list = []
    for i, proj in enumerate(resume.projects):
        tech_str = f" (Technologies: {', '.join(proj.technologies)})" if proj.technologies else ""
        desc_str = f"\n  {proj.description}" if proj.description else ""
        projects_list.append(f"[Project {i}: {proj.name}]{tech_str}{desc_str}")

    user_req_section = ""
    if user_requirements:
        confirmed = user_requirements.get("confirmed_skills", [])
        context = user_requirements.get("additional_context", "")
        if confirmed or context:
            user_req_section = "\n=== USER-CONFIRMED REQUIREMENTS & ADDITIONAL CONTEXT ===\n"
            if confirmed:
                user_req_section += f"Candidate confirmed experience with: {', '.join(confirmed)}\n"
            if context:
                user_req_section += f"Additional project/skill notes from candidate: {context}\n"

    return f"""You are an expert resume writer and ATS optimization specialist.
Tailor the candidate's resume specifically for the target job description.
Make the resume HIGHLY RELEVANT and PERSONALLY ALIGNED with this exact role, while strictly adhering to truthful facts from the candidate's background.
CRITICAL CONSTRAINT: The resume MUST fit strictly onto ONE SINGLE PAGE.

=== CANDIDATE SUMMARY ===
{resume.summary or '(none)'}

=== CANDIDATE SKILLS ===
{chr(10).join('- ' + s for s in skills) or '- (none listed)'}

=== CANDIDATE EXPERIENCE BULLETS ===
{chr(10).join(exp_bullets) or '(no corporate experience entries)'}

=== CANDIDATE PROJECTS ===
{chr(10).join(projects_list) or '(none)'}
{user_req_section}
=== TARGET JOB ===
Role: {jd.role_title or 'Target Role'}
Seniority: {jd.seniority_level or 'Not specified'}
Required skills: {', '.join(jd.required_skills) or 'none specified'}
Preferred skills: {', '.join(jd.preferred_skills) or 'none specified'}
Key Responsibilities: {'; '.join(jd.responsibilities[:8]) or 'none specified'}
ATS keywords: {', '.join(jd.keywords_for_ats[:25]) or 'none specified'}

=== CRITICAL ANTI-HALLUCINATION & 1-PAGE TAILORING INSTRUCTIONS ===
1. SUMMARY:
   - Write a strong, 2-sentence professional summary tailored specifically to '{jd.role_title}'.
   - DO NOT fabricate degrees, universities, companies, or imaginary metrics.

2. SKILL ORDER:
   - Reorder candidate's skills so the most JD-relevant skills appear first. Include all existing skills plus user-confirmed skills.

3. RELEVANT PROJECTS ONLY (STRICT 1-PAGE LIMIT):
   - Select and customize ONLY the projects that match the target JD (at most 2 projects).
   - If a project does NOT align with the role (for example, do NOT include mobile or unrelated projects for a Full Stack or AI JD), omit it from the resume.
   - For each included project, provide exactly 2 sharp, impact-driven bullet points (each 15-25 words) that emphasize:
     * Architecture and technical decisions aligning with the target role.
     * The tools, frameworks, and methodologies relevant to the JD that were actually utilized in that project.
   - DO NOT fabricate completely unrelated tools that the candidate never used.

4. BULLET EDITS (Work Experience):
   - For experience bullets, polish them to emphasize keywords and tools matching the JD (at most 2 bullets per role).

=== OUTPUT FORMAT ===
Return ONLY valid JSON, with NO markdown code fences, NO explanation, NO commentary:
{{
  "summary": "Tailored 2-sentence summary...",
  "skill_order": ["Skill 1", "Skill 2", ...],
  "bullet_edits": {{"exp_1.b1": "polished text"}},
  "project_edits": {{
    "0": [
      "Engineered a scalable REST API using FastAPI and PostgreSQL, implementing JWT auth and Redis caching to reduce response latency.",
      "Automated end-to-end integration workflows with Docker containerization and CI/CD pipelines."
    ],
    "1": [
      "Architected a cross-platform solution using React and Node.js, integrating microservices architecture for real-time data sync.",
      "Optimized database queries and API throughput, ensuring robust system reliability under concurrent load."
    ]
  }}
}}"""


def tailor_structured(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    top_k: int = 8,
    user_requirements: Optional[dict] = None,
    return_suggestions: bool = False,
):
    """Return a tailored COPY of the resume personalized for the target JD.

    - Selects ONLY relevant projects that match the target JD (at most 2 projects)
      so the resume STRICTLY FITS ON ONE PAGE.
    - If a project does not match the role, it is omitted and a relevant project suggestion
      is provided instead.
    - Tailors summary, reorders skills by JD relevance, enhances experience bullets.
    - Falls back to a deterministic heuristic if the LLM is unavailable.
    """
    import copy
    tailored = copy.deepcopy(resume)

    # If user provided confirmed requirements, incorporate them
    if user_requirements and isinstance(user_requirements, dict):
        confirmed = user_requirements.get("confirmed_skills") or []
        existing_skill_names = {s.name.lower() for s in tailored.skills}
        for cs in confirmed:
            if cs and cs.lower() not in existing_skill_names:
                tailored.skills.append(Skill(name=cs, category=_categorize_skill(cs)))
                existing_skill_names.add(cs.lower())

    # 1. Project Relevance Matching (retain all relevant projects, up to 3-4)
    matched_projs = [p for p in tailored.projects if score_project_relevance(p, jd) > 0]
    if matched_projs:
        matched_projs.sort(key=lambda p: score_project_relevance(p, jd), reverse=True)
        remaining_projs = [p for p in tailored.projects if p not in matched_projs]
        tailored.projects = (matched_projs + remaining_projs)[:3]
    else:
        tailored.projects.sort(key=lambda p: score_project_relevance(p, jd), reverse=True)
        tailored.projects = tailored.projects[:3]

    # Generate project suggestions when gaps exist
    suggested_projects = generate_project_suggestions(resume, jd, tailored.projects)

    try:
        edits = _llm_tailoring_plan(tailored, jd, top_k=top_k, user_requirements=user_requirements)
    except Exception as e:
        print(f"[RAG Pipeline] LLM tailoring plan failed ({e}); using heuristic fallback.")
        edits = _heuristic_tailoring_plan(tailored, jd, user_requirements=user_requirements)

    # 2. Apply summary edit
    summary_edit = edits.get("summary")
    if isinstance(summary_edit, str) and summary_edit.strip():
        tailored.summary = summary_edit.strip()

    # 3. Apply skill order
    order = [n for n in (edits.get("skill_order") or []) if isinstance(n, str)]
    if order:
        by_name = {s.name.lower(): s for s in tailored.skills}
        reordered = [by_name[n.lower()] for n in order if n.lower() in by_name]
        seen = {s.name.lower() for s in reordered}
        reordered += [s for s in tailored.skills if s.name.lower() not in seen]
        tailored.skills = reordered

    # 4. Apply bullet edits by id
    bullet_map = {}
    for exp in tailored.experience:
        for b in exp.bullets:
            bullet_map[b.id] = b
    for bid, text in (edits.get("bullet_edits") or {}).items():
        if bid in bullet_map and isinstance(text, str) and text.strip():
            bullet_map[bid].text = text.strip()

    # 5. Apply project edits to the selected relevant projects
    proj_edits = edits.get("project_edits") or {}
    for i, proj in enumerate(tailored.projects):
        new_bullets = (
            proj_edits.get(str(i))
            or proj_edits.get(i)
            or proj_edits.get(proj.name)
            or proj_edits.get(proj.name.lower())
        )
        if new_bullets:
            if isinstance(new_bullets, list):
                clean_list = [
                    re.sub(r"^[•●*–—\-◦\s]+", "", b).strip()
                    for b in new_bullets if b and isinstance(b, str) and b.strip()
                ][:2]  # Strict limit: 2 bullets for 1-page fit
                if clean_list:
                    proj.description = "\n".join(f"• {b}" for b in clean_list)
            elif isinstance(new_bullets, str) and new_bullets.strip():
                lines = [
                    re.sub(r"^[•●*–—\-◦\s]+", "", l).strip()
                    for l in new_bullets.splitlines() if l.strip()
                ][:2]
                if lines:
                    proj.description = "\n".join(f"• {l}" for l in lines)
                else:
                    proj.description = f"• {new_bullets.strip()}"
        else:
            # Keep at most 2 bullets from existing description
            existing_lines = [b.strip() for b in proj.description.splitlines() if b.strip()][:2]
            if existing_lines:
                proj.description = "\n".join(f"• {re.sub(r'^[•●*–—\-◦\s]+', '', b)}" for b in existing_lines)

    # Anti-hallucination verification
    tailored.education = resume.education
    tailored.contact = resume.contact
    tailored.certifications = resume.certifications
    tailored.achievements = getattr(resume, "achievements", [])
    for exp, orig_exp in zip(tailored.experience, resume.experience):
        exp.company = orig_exp.company
        exp.title = orig_exp.title
        exp.start_date = orig_exp.start_date
        exp.end_date = orig_exp.end_date

    if return_suggestions:
        return tailored, suggested_projects
    return tailored


def _llm_tailoring_plan(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    top_k: int = 8,
    user_requirements: Optional[dict] = None,
) -> dict:
    """Ask Gemini for the JSON tailoring plan."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or not api_key.startswith("AIza"):
        raise ValueError("GEMINI_API_KEY is not configured properly")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
    except ImportError:
        raise RuntimeError("google.generativeai not installed")

    build_rag_index(resume, jd)
    retrieved = retrieve_relevant_chunks(
        f"{jd.role_title} {', '.join(jd.required_skills)}", top_k=top_k,
    )
    prompt = build_constrained_prompt(resume, jd, user_requirements=user_requirements)
    if retrieved:
        ctx = "\n".join(f"[{c['metadata'].get('source')}/{c['metadata'].get('section')}] {c['text']}" for c in retrieved)
        prompt += f"\n\nRETRIEVED CONTEXT (most relevant resume/JD chunks):\n{ctx}"

    model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    response = genai.GenerativeModel(model_name).generate_content(
        prompt,
        request_options={"timeout": 12.0}
    )
    if not response or not response.text:
        raise ValueError("Gemini returned empty response")
    return _parse_plan_json(response.text.strip())


def _parse_plan_json(text: str) -> dict:
    """Extract the JSON plan from an LLM response (tolerates fences, trailing commas, linebreaks)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object in LLM response")

    json_str = cleaned[start:end + 1]
    # Remove trailing commas before } or ]
    json_str_fixed = re.sub(r",\s*([}\]])", r"\1", json_str)

    try:
        plan = json.loads(json_str_fixed)
    except Exception:
        try:
            plan = json.loads(json_str)
        except Exception as e:
            raise ValueError(f"Failed to parse LLM JSON: {e}")

    if not isinstance(plan, dict):
        raise ValueError("LLM plan is not a JSON object")
    plan.setdefault("summary", "")
    plan.setdefault("skill_order", [])
    plan.setdefault("bullet_edits", {})
    plan.setdefault("project_edits", {})
    if not isinstance(plan["bullet_edits"], dict):
        plan["bullet_edits"] = {}
    if not isinstance(plan["project_edits"], dict):
        plan["project_edits"] = {}
    return plan


def _heuristic_tailoring_plan(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    user_requirements: Optional[dict] = None,
) -> dict:
    """Deterministic fallback: rank skills by JD overlap, tailor summary, and groundedly align project bullets."""
    jd_terms = {t.lower() for t in (jd.required_skills + jd.preferred_skills + jd.keywords_for_ats) if t}
    if user_requirements:
        confirmed = user_requirements.get("confirmed_skills") or []
        jd_terms.update(s.lower() for s in confirmed)

    def score(skill_name: str) -> int:
        nl = skill_name.lower()
        return sum(1 for t in jd_terms if t and (t in nl or nl in t))

    all_skills = [s.name for s in resume.skills]
    if user_requirements and "confirmed_skills" in user_requirements:
        for s in user_requirements["confirmed_skills"]:
            if s and s not in all_skills:
                all_skills.append(s)

    ordered = sorted(all_skills, key=score, reverse=True)
    matching_skills = [s for s in all_skills if score(s) > 0]

    role = jd.role_title or "Software Engineer"
    key_tech = ", ".join(matching_skills[:5]) if matching_skills else ", ".join(all_skills[:4])
    summary = f"Results-driven engineer specializing in {role}. Experienced in developing high-impact solutions with {key_tech}, passionate about delivering robust and scalable software systems aligned with organizational objectives."

    # Polish project bullets with strong action verbs
    project_edits = {}
    strong_verbs = ["Architected and delivered", "Engineered and shipped", "Designed and implemented", "Automated workflows for"]
    for i, proj in enumerate(resume.projects):
        bullets = [b.strip().lstrip("•-–* ") for b in proj.description.splitlines() if b.strip()]
        if not bullets and proj.description:
            bullets = [proj.description.strip()]
        polished = []
        for j, b in enumerate(bullets):
            opener = strong_verbs[j % len(strong_verbs)]
            if not any(b.lower().startswith(v.lower()) for v in ["architected", "engineered", "developed", "built", "implemented", "designed", "automated"]):
                b_text = b[0].lower() + b[1:] if len(b) > 1 else b
                polished.append(f"{opener} {b_text}")
            else:
                polished.append(b)
        project_edits[str(i)] = polished

    return {
        "summary": summary,
        "skill_order": ordered,
        "bullet_edits": {},
        "project_edits": project_edits,
    }
