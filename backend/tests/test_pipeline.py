from datetime import date

from common.schema.resume import (
    ResumeSchema, JointRequirementsSchema, ContactInfo, Skill,
    ExperienceEntry, ExperienceBullet, EducationEntry, ProjectEntry,
    CertificationEntry, MatchReport, PatchAction, PatchList
)
from backend.src.services.resume_parser import _extract_structured
from backend.src.services.jd_analyzer import analyze_jd
from backend.src.services.gap_analyzer import compute_match
from backend.src.services.generator import generate_patches
from backend.src.services.validator import validate_patches
from backend.src.services.renderer import _build_html, _build_context
from backend.src.api.app import _apply_patches_to_resume, app


SAMPLE_RESUME_TEXT = """
Jane Developer
jane.dev@example.com | +1 (555) 234-5678 | linkedin.com/in/janedev | github.com/janedev

SUMMARY
Full-Stack Software Engineer with 5+ years of experience in Python, TypeScript, React, and AWS cloud infrastructure.

SKILLS
Python, JavaScript, TypeScript, React, Next.js, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, GraphQL, Git

EXPERIENCE
Innovate Corp — Senior Software Engineer
Jan 2021 – Present
• Designed and deployed scalable distributed microservices in FastAPI and Docker on AWS ECS.
• Improved API response times by 35% through Redis caching and PostgreSQL query optimization.
• Mentored junior developers and established CI/CD best practices using GitHub Actions.

Startup Lab — Full Stack Developer
Mar 2019 – Dec 2020
• Built reactive frontend user interfaces in React, TypeScript, and TailwindCSS.
• Integrated third-party payment and messaging APIs using Python and Flask.

EDUCATION
University of Technology — B.S. in Computer Science (2019)

PROJECTS
CloudMetrics
Real-time infrastructure monitoring dashboard using Python, React, and Redis.

CERTIFICATIONS
AWS Certified Solutions Architect (2022)
"""

SAMPLE_JD_TEXT = """
Job Title: Senior Backend Engineer
Seniority: Senior
Location: Remote

We are seeking a talented Senior Backend Engineer with 4+ years of professional experience.

Responsibilities:
• Architect, implement, and maintain highly available cloud microservices in Python.
• Work with PostgreSQL, Redis, Docker, Kubernetes, and AWS infrastructure.
• Drive engineering excellence, automated testing, and CI/CD pipelines.

Required Skills:
Python, FastAPI, AWS, Docker, Kubernetes, PostgreSQL

Nice to Have:
Redis, GraphQL, TypeScript
"""


def test_resume_parser_structured():
    resume = _extract_structured(SAMPLE_RESUME_TEXT)
    assert resume.contact.name == "Jane Developer"
    assert resume.contact.email == "jane.dev@example.com"
    assert len(resume.skills) >= 5
    assert any(s.name == "Python" for s in resume.skills)
    assert len(resume.experience) >= 2
    assert resume.experience[0].company != ""
    assert len(resume.experience[0].bullets) >= 2
    assert len(resume.education) >= 1
    assert len(resume.projects) >= 1
    assert len(resume.certifications) >= 1


def test_jd_analyzer():
    jd = analyze_jd(SAMPLE_JD_TEXT)
    assert "Senior" in jd.role_title or "Engineer" in jd.role_title
    assert jd.seniority_level == "senior"
    assert "Python" in jd.required_skills
    assert "AWS" in jd.required_skills
    assert jd.min_years_experience >= 4
    assert len(jd.responsibilities) >= 1


def test_gap_analyzer():
    resume = _extract_structured(SAMPLE_RESUME_TEXT)
    jd = analyze_jd(SAMPLE_JD_TEXT)
    match = compute_match(resume, jd)

    assert 0 <= match.overall_score <= 100
    assert 0.0 <= match.keyword_coverage <= 1.0
    assert 0.0 <= match.experience_match <= 1.0
    assert isinstance(match.gaps, list)
    assert isinstance(match.suggestions, list)


def test_generator_and_validator():
    resume = _extract_structured(SAMPLE_RESUME_TEXT)
    jd = analyze_jd(SAMPLE_JD_TEXT)
    match = compute_match(resume, jd)

    patches = generate_patches(resume, jd, match)
    assert len(patches.patches) > 0

    validated = validate_patches(resume, patches)
    assert len(validated.patches) > 0


def test_apply_patches_and_rendering():
    resume = _extract_structured(SAMPLE_RESUME_TEXT)
    jd = analyze_jd(SAMPLE_JD_TEXT)
    match = compute_match(resume, jd)
    patches = generate_patches(resume, jd, match)
    validated = validate_patches(resume, patches)

    tailored = _apply_patches_to_resume(resume, validated.patches)
    assert tailored.contact.name == resume.contact.name
    assert len(tailored.skills) > 0

    html = _build_html(tailored)
    assert "Jane Developer" in html
    assert "jane.dev@example.com" in html
    assert "Skills" in html
    assert "Experience" in html
