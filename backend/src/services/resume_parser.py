"""Resume parser — extracts structured data from PDF/DOCX text."""
import re
from datetime import date
from typing import Optional

from ..models.resume import (
    ResumeSchema, ContactInfo, Skill, ExperienceBullet,
    ExperienceEntry, EducationEntry, ProjectEntry, CertificationEntry,
)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def parse_pdf(path: str) -> ResumeSchema:
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required. Install: pip install pdfplumber")

    # Clean up well-known PDF extraction artifacts BEFORE running the
    # structured extractor, so that bullet characters encoded as
    # "(cid:127)" or Unicode replacement markers don't end up as
    # literal text and confuse the section segmentation.
    full_text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                full_text += t + "\n"
    full_text = _clean_pdf_artifacts(full_text)
    return _extract_structured(full_text)


def _clean_pdf_artifacts(text: str) -> str:
    """Strip common PDF extraction artifacts.

    Replaces bullet glyphs and custom font codepoints with standard bullets or dashes,
    and cleans up common font encoding issues.
    """
    # Bullet codepoints in embedded fonts
    text = re.sub(r"\(cid:127\)", "•", text)
    text = text.replace("\xa7", " – ")
    text = text.replace("\ufffd", " – ")
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "–").replace("\u2014", "–")
    text = re.sub(r"^[ \t]*[•●◆■○▶►▸▪➤→*◦]+[ \t]*", "• ", text, flags=re.M)
    # Strip phone-link artifacts like "n " and " & " that pdfplumber
    # sometimes injects from the contact area
    text = re.sub(r"^[ \t]*[&n][ \t]+", "", text, flags=re.M)
    return text


def parse_docx(path: str) -> ResumeSchema:
    try:
        from docx import Document
    except ImportError:
        raise ImportError("python-docx is required. Install: pip install python-docx")

    doc = Document(path)

    # Build a flat text stream that preserves section headers BEFORE any
    # table content. We walk the body XML element-by-element so that a
    # paragraph ("PROJECTS") followed by a <w:tbl> still emits the header
    # text before the table cell text.
    chunks: list[str] = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            for p in doc.paragraphs:
                if p._element is child:
                    chunks.append(p.text)
                    break
        elif tag == "tbl":
            # Emit each table as a special marker block the extractor can pick up
            chunks.append("[[TABLE_BEGIN]]")
            for tbl in doc.tables:
                if tbl._element is child:
                    for row in tbl.rows:
                        for cell in row.cells:
                            for p in cell.paragraphs:
                                chunks.append(p.text)
                            chunks.append("[[CELL]]")
                        chunks.append("[[ROW_END]]")
                    break
            chunks.append("[[TABLE_END]]")
    full_text = "\n".join(chunks)
    return _extract_structured(full_text)


# ---------------------------------------------------------------------------
# Section header patterns — deliberately broad to catch real-world resumes
# ---------------------------------------------------------------------------

_SECTION_PATTERNS: dict[str, re.Pattern] = {
    "summary": re.compile(
        r"^\s*(summary|professional\s+summary|career\s+summary|objective|"
        r"career\s+objective|profile|about\s+me|overview)\s*$", re.I
    ),
    "skills": re.compile(
        r"^\s*(skills|technical\s+skills|core\s+(?:skills|competencies)|"
        r"key\s+skills|technologies|tools?\s+&?\s*technologies?|"
        r"technical\s+expertise|competencies|areas\s+of\s+expertise)\s*$", re.I
    ),
    "experience": re.compile(
        r"^\s*(experience|work\s+experience|professional\s+experience|"
        r"employment|employment\s+history|work\s+history|career\s+history|"
        r"relevant\s+experience|internship|internships)\s*$", re.I
    ),
    "education": re.compile(
        r"^\s*(education|academic|academic\s+(?:background|history)|"
        r"qualifications|educational\s+background|degrees?)\s*$", re.I
    ),
    "projects": re.compile(
        r"^\s*(projects?|personal\s+projects?|side\s+projects?|"
        r"academic\s+projects?|key\s+projects?|notable\s+projects?|"
        r"portfolio|selected\s+projects?|open\s+source)\s*$", re.I
    ),
    "achievements": re.compile(
        r"^\s*(achievements?|key\s+achievements?|awards?|honors?|"
        r"honors?\s*(?:&|and)?\s*awards?|awards?\s*(?:&|and)?\s*honors?|"
        r"accomplishments?|recognitions?|competitions?|hackathons?)\s*$", re.I
    ),
    "certifications": re.compile(
        r"^\s*(certifications?|certificates?|licenses?|credentials?|"
        r"professional\s+certifications?|online\s+courses?)\s*$", re.I
    ),
    "languages": re.compile(
        r"^\s*(languages?|spoken\s+languages?|language\s+proficiency)\s*$", re.I
    ),
    "interests": re.compile(
        r"^\s*(interests?|hobbies?|activities|extracurricular)\s*$", re.I
    ),
}

_DATE_RANGE_RE = re.compile(
    r"(\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    r"[\s,]*\d{2,4}|\d{4})"
    r"\s*[-–—to]+\s*"
    r"(present|current|\b(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|"
    r"dec(?:ember)?)[\s,]*\d{2,4}|\d{4})",
    re.I,
)

_BULLET_CHARS = r"•●◆■○▶►▸▪➤→\-–—*◦"
_BULLET_RE = re.compile(rf"^[{_BULLET_CHARS}]\s*|^\d+[\.\)]\s*")

_TECH_SKILLS = {
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C#",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "Bash", "Shell",
    "React", "Vue", "Angular", "Next.js", "Node.js", "Express", "Django",
    "Flask", "FastAPI", "Spring", "Rails", "Laravel", "Svelte", "NestJS",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Ansible",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka", "Elasticsearch",
    "GraphQL", "REST", "REST API", "gRPC", "SQL", "NoSQL", "SQLite",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Spark",
    "LangChain", "LLM", "LLMs", "RAG", "NLP", "OpenCV", "YOLO",
    "Deep Learning", "Machine Learning", "Computer Vision", "CNN", "RNN",
    "Vector Database", "ChromaDB", "Pinecone", "Weaviate", "Hugging Face",
    "Transformers", "Keras", "Tailwind", "Microservices", "Raspberry Pi", "IoT",
    "MLOps", "Prompt Engineering", "Git", "Linux", "Nginx", "Jenkins",
    "GitHub Actions", "CI/CD", "Agile", "Scrum", "Jira", "Figma",
}


# ---------------------------------------------------------------------------
# Core extractor
# ---------------------------------------------------------------------------

def _extract_structured(text: str) -> ResumeSchema:
    lines = text.splitlines()

    contact = _extract_contact(lines[:20])

    # Segment lines into named sections
    sections: dict[str, list[str]] = {"header": []}
    current_section = "header"

    for line in lines:
        stripped = line.strip()
        matched_section = None
        for sec_name, pat in _SECTION_PATTERNS.items():
            if pat.match(stripped):
                matched_section = sec_name
                break

        if matched_section:
            current_section = matched_section
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(line)

    summary       = _extract_summary(sections.get("summary", []))
    skills        = _extract_skills(sections.get("skills", []))
    experience    = _extract_experience(sections.get("experience", []))
    education     = _extract_education(sections.get("education", []))
    projects      = _extract_projects(sections.get("projects", []))
    raw_certs = _extract_certifications(
        sections.get("certifications", []) +
        sections.get("languages", []) +   # keep languages as certs so they appear
        sections.get("interests", [])
    )
    raw_achs = _extract_certifications(sections.get("achievements", []))

    _ACH_KEYWORDS = (
        "place", "award", "winner", "win", "won", "hackathon", "selected", "founded",
        "patent", "published", "rank", "finalist", "prize", "champion", "runner-up",
        "runner up", "competition", "contest", "medal", "trophy", "scholarship",
        "fellowship", "merit", "honor", "honour", "innovates", "national", "state-level",
        "college-level", "ctf", "olympiad", "all india rank",
    )
    def _is_ach(entry: CertificationEntry) -> bool:
        blob = f"{entry.name} {entry.issuer}".lower()
        return any(k in blob for k in _ACH_KEYWORDS)

    all_items = raw_achs + raw_certs
    achievements: list[CertificationEntry] = []
    certifications: list[CertificationEntry] = []
    for item in all_items:
        if _is_ach(item):
            achievements.append(item)
        else:
            certifications.append(item)

    return ResumeSchema(
        contact=contact,
        summary=summary,
        skills=skills,
        experience=experience,
        education=education,
        projects=projects,
        certifications=certifications,
        achievements=achievements,
    )


# ---------------------------------------------------------------------------
# Section extractors
# ---------------------------------------------------------------------------

def _extract_contact(lines: list[str]) -> ContactInfo:
    full_text = "\n".join(lines)

    SECTION_NAMES = {"technical skills", "skills", "experience", "education", "projects", "certifications", "summary", "work experience", "professional summary"}
    name = ""
    for line in lines[:8]:
        s = line.strip()
        if not s or s.lower() in SECTION_NAMES:
            continue
        if "@" in s or "http" in s or ".com" in s or re.search(r"\d{4}", s):
            continue
        m = re.match(r"^([A-Z][a-zA-Z\-']+(?:\s+[A-Z][a-zA-Z\-']+){0,3})\s*$", s)
        if m and len(m.group(1)) >= 3 and m.group(1).lower() not in SECTION_NAMES:
            name = m.group(1).strip()
            break
    if not name:
        m = re.search(r"([A-Z][a-z]+ (?:[A-Z][a-z]+ )?[A-Z][a-z]+)", full_text)
        if m and m.group(1).lower() not in SECTION_NAMES:
            name = m.group(1).strip()

    email_m   = re.search(r"[\w.+-]+@[\w.-]+\.\w{2,}", full_text)
    phone_m   = re.search(r"[\+\d][\d\s\-\(\)\.]{7,15}\d", full_text)
    linkedin  = re.search(r"linkedin\.com/in/[\w\-]+", full_text, re.I)
    github    = re.search(r"github\.com/[\w\-]+", full_text, re.I)
    portfolio = re.search(r"https?://[\w\.\-/]+(?:portfolio|personal|me|dev|io)[\w\.\-/]*", full_text, re.I)

    links: list[str] = []
    if linkedin:  links.append(linkedin.group())
    if github:    links.append(github.group())
    if portfolio and portfolio.group() not in " ".join(links):
        links.append(portfolio.group())

    return ContactInfo(
        name=name,
        email=email_m.group().strip() if email_m else "",
        phone=phone_m.group().strip() if phone_m else "",
        links=links,
    )


def _extract_summary(lines: list[str]) -> str:
    text = " ".join(l.strip() for l in lines if l.strip())
    return text[:1200]


def _extract_skills(lines: list[str]) -> list[Skill]:
    """Extract skills ONLY from the dedicated Skills section. No full-text scan."""
    skills: dict[str, Skill] = {}

    # Multi-character skills that contain slashes, dots, or other
    # characters that the splitter would otherwise break on. We
    # protect these by replacing the splitter-internal character with
    # a placeholder before splitting, then restoring.
    _PROTECTED = {
        "ci/cd": "CI⧸CD",
        "ci-cd": "CI-CD",
        "c++":   "C⧸⧸",
        "c#":    "C♯",
        ".net":  "⧸NET",
        "vue.js": "VUE⧸JS",
        "node.js": "NODE⧸JS",
        "next.js": "NEXT⧸JS",
        "nuxt.js": "NUXT⧸JS",
        "d3.js":  "D3⧸JS",
        "rxjs":   "RXJS",
    }
    _RESTORE = {v: k for k, v in _PROTECTED.items()}

    def _protect(text: str) -> str:
        out = text
        for original, placeholder in _PROTECTED.items():
            out = re.sub(r"(?i)" + re.escape(original), placeholder, out)
        return out

    def _restore(name: str) -> str:
        out = name
        for placeholder, original in _RESTORE.items():
            out = out.replace(placeholder, original)
        # Normalize display form for known protected skills
        if out.lower() == "ci⧸cd" or out.lower() == "ci-cd":
            return "CI/CD"
        if out.lower() == "c⧸⧸":
            return "C++"
        if out.lower() == "c♯":
            return "C#"
        return out

    for line in lines:
        # Strip common category labels like "Languages: Python, Java"
        # by splitting on the first colon if the part before it is short
        if ":" in line:
            colon_idx = line.index(":")
            label = line[:colon_idx].strip()
            rest  = line[colon_idx+1:]
            # If the label looks like a category (short, no spaces or ≤ 4 words)
            if len(label) < 35 and len(label.split()) <= 4:
                line = rest  # only parse the values, not the label

        protected_line = _protect(line)
        parts = re.split(r"[,;|•·\t]+", protected_line)
        for part in parts:
            name = _restore(part).strip().strip(":-– ()")
            # Keep names between 2 and 40 chars; skip obvious noise
            if 1 < len(name) < 40 and not re.match(r"^\d+$", name):
                cat = _categorize_skill(name)
                skills[name.lower()] = Skill(name=name, category=cat)

    return list(skills.values())[:30]


def _categorize_skill(name: str) -> str:
    nl = name.lower()
    if any(k in nl for k in ["python", "javascript", "typescript", "java", "golang",
                               "rust", "c++", "c#", "ruby", "php", "swift", "kotlin",
                               "scala", "bash", "shell", "matlab", "r language"]):
        return "language"
    if any(k in nl for k in ["react", "vue", "angular", "next", "node", "django",
                               "flask", "fastapi", "spring", "rails", "laravel",
                               "express", "svelte", "nest"]):
        return "framework"
    if any(k in nl for k in ["aws", "azure", "gcp", "docker", "kubernetes", "terraform",
                               "ansible", "ci/cd", "jenkins", "github actions", "linux",
                               "nginx", "heroku", "vercel"]):
        return "devops"
    if any(k in nl for k in ["postgres", "mysql", "mongo", "redis", "sql", "elastic",
                               "kafka", "sqlite", "dynamodb", "firebase", "supabase"]):
        return "database"
    if any(k in nl for k in ["tensorflow", "pytorch", "scikit", "pandas", "numpy",
                               "spark", "hugging", "transformers", "nlp", "ml", "ai"]):
        return "ml/ai"
    return "general"


def _extract_experience(lines: list[str]) -> list[ExperienceEntry]:
    entries: list[ExperienceEntry] = []
    exp_idx     = 0
    current_entry: Optional[dict] = None
    bullets: list[ExperienceBullet] = []
    bullet_idx  = 0
    prev_header_line = ""

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        date_match = _DATE_RANGE_RE.search(stripped)
        is_bullet  = bool(_BULLET_RE.match(stripped)) or (
            len(stripped) > 20 and stripped[0].islower() and not date_match
        )

        if date_match and len(stripped) < 130 and not is_bullet:
            # Flush previous entry
            if current_entry is not None:
                exp_idx += 1
                entries.append(ExperienceEntry(
                    id=f"exp_{exp_idx}",
                    company=current_entry.get("company", ""),
                    title=current_entry.get("title", ""),
                    start_date=current_entry.get("start_date"),
                    end_date=current_entry.get("end_date"),
                    current=current_entry.get("current", False),
                    bullets=bullets,
                ))
                bullets    = []
                bullet_idx = 0

            start_str, end_str = date_match.group(1), date_match.group(2)
            company_candidate  = stripped[:date_match.start()].strip(" |-–—,()")

            if not company_candidate and prev_header_line:
                company_candidate = prev_header_line

            company, title = _split_company_title(company_candidate)

            current_entry = {
                "company":    company,
                "title":      title,
                "start_date": _parse_partial_date(start_str),
                "end_date":   None if re.search(r"present|current", end_str, re.I)
                              else _parse_partial_date(end_str),
                "current":    bool(re.search(r"present|current", end_str, re.I)),
            }
            prev_header_line = ""

        elif is_bullet:
            if current_entry is not None:
                bullet_idx += 1
                exp_ref     = f"exp_{exp_idx + 1}"
                bullet_text = _BULLET_RE.sub("", stripped).strip()
                bullets.append(ExperienceBullet(
                    id=f"{exp_ref}.b{bullet_idx}",
                    text=bullet_text,
                ))
        else:
            if current_entry is not None and not current_entry.get("title"):
                if len(stripped) < 80:
                    current_entry["title"] = stripped
            else:
                prev_header_line = stripped

    # Flush last entry
    if current_entry is not None:
        exp_idx += 1
        entries.append(ExperienceEntry(
            id=f"exp_{exp_idx}",
            company=current_entry.get("company", ""),
            title=current_entry.get("title", ""),
            start_date=current_entry.get("start_date"),
            end_date=current_entry.get("end_date"),
            current=current_entry.get("current", False),
            bullets=bullets,
        ))

    return entries


def _split_company_title(text: str) -> tuple[str, str]:
    """Split 'Company — Title' or 'Title at Company' into (company, title)."""
    if not text:
        return "", ""
    for sep in ("—", " - ", " | ", " · "):
        if sep in text:
            parts = text.split(sep, 1)
            return parts[0].strip(), parts[1].strip()
    if re.search(r"\bat\b", text, re.I):
        idx = re.search(r"\bat\b", text, re.I).start()
        return text[idx+2:].strip(), text[:idx].strip()
    # No separator — treat entire string as company name
    return text.strip(), ""


def _parse_partial_date(s: str) -> Optional[date]:
    s = s.strip()
    m = re.fullmatch(r"(\d{4})", s)
    if m:
        return date(int(m.group(1)), 1, 1)
    m = re.search(
        r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]+(\d{4})", s, re.I
    )
    if m:
        abbr_to_num = {
            "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
            "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        }
        month = abbr_to_num.get(m.group(1).lower()[:3], 1)
        return date(int(m.group(2)), month, 1)
    return None


def _extract_education(lines: list[str]) -> list[EducationEntry]:
    entries: list[EducationEntry] = []
    current: Optional[dict]       = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        date_m = re.search(r"\d{4}", stripped)
        is_school = re.search(
            r"\b(university|college|institute|school|academy|"
            r"b\.?s\.?c?|m\.?s\.?c?|b\.?e\.?|m\.?e\.?|"
            r"phd|ph\.d|bachelor|master|degree|b\.?tech|m\.?tech|"
            r"b\.?a\.?|m\.?a\.?|mba|diploma)\b",
            stripped, re.I
        )
        if is_school:
            if current:
                entries.append(EducationEntry(**current))
            current = {
                "school": stripped,
                "degree": "",
                "dates":  date_m.group() if date_m else "",
                "gpa":    None,
            }
        elif current:
            # GPA line
            gpa_m = re.search(r"gpa[:\s]+(\d+\.?\d*)", stripped, re.I)
            if gpa_m:
                current["gpa"] = gpa_m.group(1)
            elif not current.get("degree") and len(stripped) < 120:
                current["degree"] = stripped

    if current:
        entries.append(EducationEntry(**current))

    return entries


def _extract_projects(lines: list[str]) -> list[ProjectEntry]:
    """Extract projects — handles table layout, titled blocks, and bullet lists.

    Supports DOCX tables (marker-based), flat-text 2-column layouts, and
    titled block layouts with tags and bullet points.
    """
    # ── Path 1: DOCX table layout (marker-based) ───────────────────────────
    if any(l.strip() == "[[TABLE_BEGIN]]" for l in lines):
        return _extract_projects_from_table(lines)

    # ── Path 2: Comprehensive block and bullet layout ──────────────────────
    return _extract_projects_from_blocks(lines)


def _looks_like_project_title_line(line: str) -> bool:
    """A project title line in the PDF flat-text layout is one that contains
    a '|' separator followed by a '·' delimiter, e.g.
        'Symbol Detection ML Model | Python · YOLO · OpenCV · TensorFlow'
    """
    s = line.strip()
    if "|" not in s:
        return False
    if "·" not in s and "•" not in s:
        return False
    return True


def _extract_projects_from_pdf_layout(lines: list[str]) -> list[ProjectEntry]:
    """Parse projects from a PDF where the table is rendered as a 2-column
    flat-text stream. A project title line contains ' | tag1 · tag2 · tag3'.
    Preceding lines (date, type label like 'Personal Project') and following
    lines (description paragraphs) belong to the same project until the next
    title line appears.

    Common PDF artifact: a left-column label like 'Robocon 2026 (AIR 21 -'
    gets concatenated by pdfplumber with the right-column first description
    line. We detect and strip that prefix.
    """
    entries: list[ProjectEntry] = []
    current: Optional[dict] = None
    description_buffer: list[str] = []

    def flush():
        if current is not None:
            current["description"] = " ".join(description_buffer).strip()
            entries.append(ProjectEntry(**current))

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip section headers and section-tail noise
        if _SECTION_PATTERNS["projects"].match(stripped):
            continue

        if _looks_like_project_title_line(stripped):
            flush()
            # New project — split title and tags
            name, tags = _split_title_and_tags(stripped)
            # Strip a leading date range from the title ("2025 - 2026 Symbol...")
            name = _strip_leading_date_range(name)
            current = {
                "name":         name or stripped[:60],
                "description":  "",
                "technologies": _extract_tags_as_technologies(tags) if tags else [],
                "url":          "",
            }
            description_buffer = []
            continue

        # Continuation of current project
        if current is not None:
            # Strip any left-column noise that has been concatenated to this line
            cleaned = _strip_left_column_prefix(stripped)
            if not cleaned:
                continue
            description_buffer.append(cleaned)
            # Pick up any tech keywords in the description body
            for tech in _TECH_SKILLS:
                if re.search(r"\b" + re.escape(tech) + r"\b", cleaned, re.I):
                    if tech not in current["technologies"]:
                        current["technologies"].append(tech)
        # If no current and line is not a title, skip (likely a stray header)

    flush()
    return entries


_DATE_RANGE_AT_START = re.compile(r"^\s*\d{4}\s*[–—-]\s*\d{4}\s+")
_YEAR_ONLY_AT_START  = re.compile(r"^\s*\d{4}\s+")


def _strip_leading_date_range(text: str) -> str:
    """Remove a leading '2025 - 2026' or '2025' date prefix from a project title."""
    text = _DATE_RANGE_AT_START.sub("", text, count=1)
    text = _YEAR_ONLY_AT_START.sub("", text, count=1)
    return text.strip()


# Lines that pdfplumber creates by concatenating the LEFT column of a 2-column
# table with the right column. These prefixes should be stripped.
_LEFT_COL_PREFIX_PATTERNS = [
    re.compile(r"^\s*\d{4}\s*[–—-]\s*\d{4}\s*"),  # 2025 - 2026
    re.compile(r"^\s*\d{4}\s+"),                    # 2025
    # (AIR 21 – Developed...) — the "(AIR" is leftover from the left column
    re.compile(r"^\s*\(?\s*(?:AIR|All\s+India\s+Rank)\s*\d+[^)]*\)?\s*[–—-]?\s*", re.I),
    # The full contest label from left column
    re.compile(r"^\s*(?:Robocon|India\s+Innovates|AI\s+Drone|Smart\s+Crop|Aqua\s+Cleaner)\b[^()]*?\(?AIR[^()]*?\)\s*", re.I),
    # "Robocon 2026 (AIR 21 -" — but only strip the label part, not the description
    re.compile(r"^\s*(?:Robocon|India\s+Innovates)[^()]*?\(?AIR[^()]*?\)\s*[–—-]?\s*", re.I),
    re.compile(r"^\s*(?:AIR|All\s+India\s+Rank)[^()]*?\)?\s*[–—-]?\s*", re.I),
    # "Personal Project" / "Academic Project" / etc.
    re.compile(r"^\s*Personal\s+Project\s*", re.I),
    re.compile(r"^\s*Academic\s+Project\s*", re.I),
    re.compile(r"^\s*Side\s+Project\s*", re.I),
    re.compile(r"^\s*Open\s+Source\s*", re.I),
    # Parenthetical contest results left behind
    re.compile(r"^\s*\(?\s*(?:Finalist|Winner|Runner-?up|National|International|India|Hackathon)[a-zA-Z\s-]*\)\s*", re.I),
    # "(Finalist)" that runs into the next word ("classification")
    re.compile(r"^\s*\(?(?:Finalist|AIR)\)\s*", re.I),
]


def _strip_left_column_prefix(line: str) -> str:
    """Try to strip any left-column noise from a project description line.
    Returns the cleaned line, or '' if the line was entirely noise. The loop
    strips prefixes repeatedly until no more match — handles cases like
    'Robocon 2026 (AIR 21 -' + 'National)' where two patterns need to apply.
    """
    cleaned = line
    for _ in range(8):  # enough passes to chew through any stacked prefix
        prev = cleaned
        for pat in _LEFT_COL_PREFIX_PATTERNS:
            new = pat.sub("", cleaned, count=1)
            if new != cleaned:
                cleaned = new.strip()
                break
        if cleaned == prev:
            break
    return cleaned.strip()
    return _extract_projects_from_blocks(lines)


def _extract_projects_from_table(lines: list[str]) -> list[ProjectEntry]:
    """Parse projects from a DOCX table layout.

    Each row in the table is one project. The right cell contains:
        Line 1: "Project Name | tag1 · tag2 · tag3"
        Line 2+: free-form description
    The left cell contains date range and (optionally) a project-type label
    like "Personal Project" or competition context.
    """
    entries: list[ProjectEntry] = []

    # Collect the table cells row by row
    rows: list[list[list[str]]] = []  # rows[ri][ci] = list of paragraph text
    current_row: list[list[str]] = []
    current_cell: list[str] = []

    for line in lines:
        s = line.strip()
        if s == "[[TABLE_BEGIN]]":
            current_row = []
            current_cell = []
            continue
        if s == "[[CELL]]":
            current_row.append(current_cell)
            current_cell = []
            continue
        if s == "[[ROW_END]]":
            if current_row:
                rows.append(current_row)
            current_row = []
            current_cell = []
            continue
        if s == "[[TABLE_END]]":
            if current_row:
                rows.append(current_row)
            break
        # Regular text line
        if s == "[[TABLE_BEGIN]]" or s == "[[TABLE_END]]":
            continue
        current_cell.append(s)

    for row in rows:
        if not row:
            continue
        # Right cell is usually the last (and most textually dense) cell
        right = max(row, key=lambda c: sum(len(p) for p in c)) if len(row) >= 2 else row[-1]
        right_paras = [p for p in right if p]

        if not right_paras:
            continue

        title_line = right_paras[0]
        name, tags = _split_title_and_tags(title_line)
        description = "\n".join(p.strip() for p in right_paras[1:] if p.strip()).strip()

        technologies = _extract_tags_as_technologies(tags) if tags else []
        # Also pick up tech keywords that appear in the description
        for tech in _TECH_SKILLS:
            if re.search(r"\b" + re.escape(tech) + r"\b", description, re.I):
                if tech not in technologies:
                    technologies.append(tech)

        entries.append(ProjectEntry(
            name=name or title_line[:60],
            description=description,
            technologies=technologies,
            url="",
        ))

    return entries


def _split_title_and_tags(line: str) -> tuple[str, list[str]]:
    """Split 'Symbol Detection ML Model | Python · YOLO · TensorFlow' into
    (name, [tag1, tag2, ...])."""
    # Common separators: |  ·  ‧  •  ,
    if "|" in line:
        name_part, _, tags_part = line.partition("|")
    else:
        # Fall back to last " · " split if there's no "|"
        parts = re.split(r"\s+·\s+|\s+•\s+", line)
        if len(parts) >= 2:
            name_part = parts[0]
            tags_part = " · ".join(parts[1:])
        else:
            return line.strip(), []

    name = name_part.strip()
    tags = [t.strip() for t in re.split(r"[·••|]", tags_part) if t.strip()]
    return name, tags


def _extract_tags_as_technologies(tags: list[str]) -> list[str]:
    """Convert raw tag strings into a deduped list, preferring canonical
    names when a tag matches a known skill."""
    out: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if not tag:
            continue
        canonical = _canonicalize_skill_name(tag)
        if canonical.lower() not in seen:
            seen.add(canonical.lower())
            out.append(canonical)
    return out


def _canonicalize_skill_name(tag: str) -> str:
    """Map a free-form tag to a canonical name from _TECH_SKILLS when possible,
    otherwise return the tag as-is with light cleanup. Uses word-boundary
    matching so 'Raspberry Pi' doesn't get reduced to 'R'."""
    t = tag.strip()
    # Exact (case-insensitive) match first
    for skill in _TECH_SKILLS:
        if t.lower() == skill.lower():
            return skill
    # Word-boundary match: the tag fully contains a known skill
    # (e.g. "TensorFlow.js" -> "TensorFlow")
    for skill in sorted(_TECH_SKILLS, key=len, reverse=True):
        if re.search(r"\b" + re.escape(skill) + r"\b", t, re.I):
            return skill
    return t


def _extract_projects_from_blocks(lines: list[str]) -> list[ProjectEntry]:
    """Parse projects from titled blocks, bullet points, and inline tag lines.

    Preserves ALL projects and ALL bullet points/sentences for each project.
    Handles dates in project titles, tech/role subheadings, and multi-line wrapped bullets.
    """
    entries: list[ProjectEntry] = []
    current: Optional[dict] = None
    bullets: list[str] = []

    def _is_tech_or_role_line(s: str) -> bool:
        if re.search(r"\brole:\s*", s, re.I):
            return True
        if "·" in s or "•" in s or "|" in s or "," in s:
            tech_matches = sum(1 for t in _TECH_SKILLS if re.search(r"\b" + re.escape(t) + r"\b", s, re.I))
            if tech_matches >= 2:
                return True
        if re.match(r"^(?:tech(?:nologies)?|tools?|stack)[:\s]", s, re.I):
            return True
        return False

    def _looks_like_project_title(s: str, next_s: str = "") -> bool:
        if bool(_BULLET_RE.match(s)) or _is_tech_or_role_line(s):
            return False
        # If line is only dates or punctuation
        if not re.search(r"[A-Za-z]{2,}", s):
            return False
        # Title must start with capital letter, digit or bracket
        if not re.match(r"^[A-Z0-9\[]", s):
            return False
        if len(s) > 110:
            return False
        # Check title indicators: separator, date at end, or followed by tech/role/bullet
        has_date = bool(re.search(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}|\b\d{4}\b", s, re.I))
        has_sep = any(sep in s for sep in ("|", "–", "—", " - ", " · "))
        is_heading_pattern = bool(next_s and (_is_tech_or_role_line(next_s) or _BULLET_RE.match(next_s)))
        return has_date or has_sep or is_heading_pattern

    def flush():
        nonlocal current, bullets
        if current is not None:
            current["description"] = "\n".join(bullets).strip()
            entries.append(ProjectEntry(**current))
            current = None
            bullets = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Skip section header lines if they appear inside
        if _SECTION_PATTERNS["projects"].match(stripped):
            continue

        next_line = ""
        for nxt in lines[i+1:]:
            if nxt.strip():
                next_line = nxt.strip()
                break

        is_bullet = bool(_BULLET_RE.match(stripped))

        if is_bullet:
            clean_b = _BULLET_RE.sub("", stripped).strip()
            if current is None:
                current = {
                    "name": "Project",
                    "description": "",
                    "technologies": [],
                    "url": "",
                }
            if clean_b:
                bullets.append(clean_b)
                for tech in _TECH_SKILLS:
                    if re.search(r"\b" + re.escape(tech) + r"\b", clean_b, re.I):
                        if tech not in current["technologies"]:
                            current["technologies"].append(tech)

        elif _looks_like_project_title(stripped, next_line):
            flush()
            # Clean title
            name = stripped
            tags: list[str] = []
            if "|" in name:
                name, tags = _split_title_and_tags(name)
            name = re.sub(r"\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[\s,]*\d{4}.*$", "", name, flags=re.I).strip()
            name = re.sub(r"\s*\d{4}\s*[-–—]\s*(?:present|\d{4}).*$", "", name, flags=re.I).strip()
            name = re.sub(r"\s+(Personal|Academic|Side Project|Personal Project)$", "", name, flags=re.I).strip()
            name = _strip_leading_date_range(name)
            name = re.sub(r"\s+[–—\-]\s+[a-z0-9\-_.]+$", "", name, flags=re.I).strip(" –—-|")
            name = re.sub(r"\s+[–—\-]\s*$", "", name).strip()

            current = {
                "name": name or stripped[:60],
                "description": "",
                "technologies": _extract_tags_as_technologies(tags) if tags else [],
                "url": "",
            }
            bullets = []

        elif _is_tech_or_role_line(stripped):
            if current is not None:
                clean_t = re.sub(r"^(?:tech(?:nologies)?|tools?|stack|role)[:\s]+", "", stripped, flags=re.I)
                raw_tags = [p.strip() for p in re.split(r"[·•|,]", clean_t) if p.strip()]
                for tag in _extract_tags_as_technologies(raw_tags):
                    if tag not in current["technologies"]:
                        current["technologies"].append(tag)
                for tech in _TECH_SKILLS:
                    if re.search(r"\b" + re.escape(tech) + r"\b", stripped, re.I):
                        if tech not in current["technologies"]:
                            current["technologies"].append(tech)

        elif current is not None and bullets:
            # Wrapped continuation line of the previous bullet point
            bullets[-1] += " " + stripped
            for tech in _TECH_SKILLS:
                if re.search(r"\b" + re.escape(tech) + r"\b", stripped, re.I):
                    if tech not in current["technologies"]:
                        current["technologies"].append(tech)

        elif current is not None and not bullets:
            # Descriptive line under project before bullets
            bullets.append(stripped)

    flush()
    return entries


def _extract_certifications(lines: list[str]) -> list[CertificationEntry]:
    """Extract certifications and achievements — handles wrapped continuation lines."""
    entries: list[CertificationEntry] = []
    seen: set[str] = set()

    for line in lines:
        stripped = line.strip().lstrip("•-–*◦▸▪ ")
        if not stripped or len(stripped) < 3:
            continue
        if any(pat.match(stripped) for pat in _SECTION_PATTERNS.values()):
            continue

        # If this is a continuation fragment of the previous entry (e.g. "bot." or "design.")
        if entries:
            last = entries[-1]
            words = stripped.split()
            if (stripped[0].islower() or (len(words) <= 3 and not re.search(r"\b(19|20)\d{2}\b", stripped) and not any(kw in stripped.lower() for kw in ["certif", "course", "award", "finalist", "hackathon", "winner", "place", "ibm", "google", "aws", "deeplearning"]))):
                last.name = f"{last.name} {stripped}".strip()
                continue

        key = stripped.lower()
        if key in seen:
            continue
        seen.add(key)

        date_m    = re.search(r"\b(19|20)\d{2}\b", stripped)
        issuer_m  = re.search(r"(?:issued\s+by|by|—|-)\s+([A-Z][\w\s&,\.]+)", stripped, re.I)
        url_m     = re.search(r"https?://\S+", stripped)

        name_clean = re.sub(r"\s*[-–—]\s*https?://\S+", "", stripped)
        name_clean = re.sub(r"\s*\b(19|20)\d{2}\b", "", name_clean).strip()

        entries.append(CertificationEntry(
            name=name_clean,
            issuer=issuer_m.group(1).strip() if issuer_m else "",
            date=date_m.group() if date_m else "",
            url=url_m.group() if url_m else "",
        ))

    return entries
