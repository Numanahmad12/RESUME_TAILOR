"""Pydantic schemas for structured resume extraction."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    links: list[str] = Field(default_factory=list)


class Skill(BaseModel):
    name: str
    category: str = "general"


class ExperienceBullet(BaseModel):
    id: str = ""
    text: str
    skills_used: list[str] = Field(default_factory=list)


class ExperienceEntry(BaseModel):
    id: str
    company: str = ""
    title: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    current: bool = False
    bullets: list[ExperienceBullet] = Field(default_factory=list)


class EducationEntry(BaseModel):
    school: str = ""
    degree: str = ""
    dates: str = ""
    gpa: Optional[str] = None


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str = ""


class CertificationEntry(BaseModel):
    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""


class ResumeSchema(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    skills: list[Skill] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)


class JointRequirementsSchema(BaseModel):
    role_title: str = ""
    seniority_level: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    min_years_experience: int = 0
    responsibilities: list[str] = Field(default_factory=list)
    keywords_for_ats: list[str] = Field(default_factory=list)


class MatchReport(BaseModel):
    overall_score: float = 0.0
    keyword_coverage: float = 0.0
    experience_match: float = 0.0
    responsibility_similarity: float = 0.0
    ats_formatting_score: float = 0.0
    impact_metrics_score: float = 0.0
    fit_verdict: str = "Moderate Fit"
    fit_summary: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    high_impact_improvements: list[str] = Field(default_factory=list)


class PatchAction(BaseModel):
    target: str  # e.g., "exp_1.b1" or "summary"
    action: str  # "rewrite", "reorder", "add_skills"
    original: str
    proposed: str
    reason: str = ""


class PatchList(BaseModel):
    patches: list[PatchAction] = Field(default_factory=list)