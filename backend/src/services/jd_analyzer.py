"""Job description analyzer that extracts structured requirements from raw JD text."""
import re
from typing import Optional

from ..models.resume import JointRequirementsSchema


_TECH_KEYWORDS = {
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C#",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    "React", "Vue", "Angular", "Next.js", "Node.js", "Express", "Django",
    "Flask", "FastAPI", "Spring", "Rails", "Laravel",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "Elasticsearch",
    "GraphQL", "REST", "REST API", "gRPC", "SQL", "NoSQL", "Postgres",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Spark",
    "LangChain", "LLM", "LLMs", "RAG", "NLP", "OpenCV", "YOLO",
    "Deep Learning", "Machine Learning", "Computer Vision", "CNN", "RNN",
    "Vector Database", "ChromaDB", "Pinecone", "Weaviate", "Hugging Face",
    "Transformers", "Keras", "Tailwind", "Microservices", "Raspberry Pi", "IoT",
    "MLOps", "Prompt Engineering", "Git", "Linux", "Nginx", "Jenkins",
    "GitHub Actions", "CI/CD",
}


def analyze_jd(text: str) -> JointRequirementsSchema:
    """Extract structured requirements from JD text using heuristics."""

    # --- Role title: try to find from first non-empty line or 'role:' pattern ---
    role_title = _extract_role_title(text)

    # --- Seniority ---
    seniority = "mid"
    if re.search(r"\b(senior|lead|principal|staff|sr\.?)\b", text, re.I):
        seniority = "senior"
    elif re.search(r"\b(junior|entry[- ]level|associate|jr\.?)\b", text, re.I):
        seniority = "junior"

    # --- Required skills: match against known tech keywords ---
    required_skills: list[str] = []
    preferred_skills: list[str] = []

    for kw in _TECH_KEYWORDS:
        if re.search(r"\b" + re.escape(kw) + r"\b", text, re.I):
            required_skills.append(kw)

    # Preferred / nice-to-have block
    preferred_block = re.search(
        r"(preferred|nice.to.have|bonus|desirable)[:\s]+(.{0,500})", text, re.I | re.S
    )
    if preferred_block:
        block_text = preferred_block.group(2)
        for kw in list(required_skills):
            if re.search(r"\b" + re.escape(kw) + r"\b", block_text, re.I):
                preferred_skills.append(kw)
        required_skills = [s for s in required_skills if s not in preferred_skills]

    # Cap lists
    required_skills = required_skills[:15]
    preferred_skills = preferred_skills[:10]

    # --- Years experience ---
    years_match = re.search(r"(\d+)\+?\s*years?\s*(?:of\s+)?(?:professional\s+)?experience", text, re.I)
    min_years = int(years_match.group(1)) if years_match else 0

    # --- Responsibilities: extract bullet lines ---
    responsibilities = _extract_responsibilities(text)

    # --- ATS keywords: union of required + preferred ---
    keywords_for_ats = list(dict.fromkeys(required_skills + preferred_skills))[:20]

    return JointRequirementsSchema(
        role_title=role_title,
        seniority_level=seniority,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_years_experience=min_years,
        responsibilities=responsibilities,
        keywords_for_ats=keywords_for_ats,
    )


def _extract_role_title(text: str) -> str:
    """Try to extract the job title from JD text."""
    # Common patterns: "Position: ...", "Job Title: ...", or first capitalised short line
    for pat in [
        r"(?:job\s+title|position|role)[:\s]+([^\n]{5,60})",
        r"(?:we are looking for|hiring a?n?)[:\s]+([^\n]{5,60})",
    ]:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1).strip()

    # Fallback: first non-empty line shorter than 80 chars with title-case
    for line in text.splitlines():
        line = line.strip()
        if 5 < len(line) < 80 and re.match(r"[A-Z]", line):
            return line

    return "Software Engineer"


def _extract_responsibilities(text: str) -> list[str]:
    """Extract bullet-point responsibilities from JD text."""
    bullets: list[str] = []

    # Find responsibilities section
    section_match = re.search(
        r"(?:responsibilities|what you.ll do|your role|duties)[:\s]*\n(.*?)(?:\n\n|\Z)",
        text, re.I | re.S
    )
    search_text = section_match.group(1) if section_match else text

    for line in search_text.splitlines():
        stripped = line.strip().lstrip("•-–*◦▸▪ ")
        if 20 < len(stripped) < 300 and not stripped.endswith(":"):
            bullets.append(stripped)
        if len(bullets) >= 15:
            break

    # Fallback: first 300 chars
    if not bullets:
        bullets = [text[:300].strip()]

    return bullets