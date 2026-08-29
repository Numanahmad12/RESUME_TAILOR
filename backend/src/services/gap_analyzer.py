"""Honest ATS & deterministic gap analysis between resume and job description."""
import re
from typing import List
from datetime import date, datetime

from ..models.resume import ResumeSchema, JointRequirementsSchema, MatchReport


def _skill_present(skill: str, resume_text: str, resume_skill_names: set) -> bool:
    """Check if a skill appears in resume text using multiple matching strategies.

    1. Exact set membership (fast path).
    2. Whole-word regex in the full resume corpus (covers bullets/projects).
    3. Fuzzy abbreviation / prefix match (e.g. "JS" → "JavaScript", "Postgres" → "PostgreSQL").
    """
    sl = skill.lower()

    # 1. Exact skill name
    if sl in resume_skill_names:
        return True

    # 2. Whole-word in full text
    if re.search(r"\b" + re.escape(sl) + r"\b", resume_text, re.I):
        return True

    # 3. Common abbreviation expansions
    _ALIASES: dict[str, list[str]] = {
        "js": ["javascript"],
        "ts": ["typescript"],
        "py": ["python"],
        "k8s": ["kubernetes"],
        "postgres": ["postgresql"],
        "postgresql": ["postgres"],
        "mongo": ["mongodb"],
        "gcp": ["google cloud"],
        "aws": ["amazon web services"],
        "ml": ["machine learning"],
        "dl": ["deep learning"],
        "nlp": ["natural language processing"],
        "cv": ["computer vision"],
        "oop": ["object oriented"],
        "rest": ["restful", "rest api"],
        "cicd": ["ci/cd", "continuous integration"],
        "ci/cd": ["cicd", "continuous integration"],
        "nodejs": ["node.js", "node js"],
        "node.js": ["nodejs"],
        "nextjs": ["next.js"],
        "next.js": ["nextjs"],
        "reactjs": ["react"],
        "react": ["reactjs"],
    }
    for alias in _ALIASES.get(sl, []):
        if re.search(r"\b" + re.escape(alias) + r"\b", resume_text, re.I):
            return True

    # 4. Partial token match — if skill is ≥5 chars and appears as a substring
    # of a resume skill name or vice versa (catches e.g. "FastAPI" ↔ "fastapi")
    if len(sl) >= 5:
        for rsn in resume_skill_names:
            if sl in rsn or rsn in sl:
                return True

    return False


def compute_match(resume: ResumeSchema, jd: JointRequirementsSchema) -> MatchReport:
    """Compute comprehensive, honest ATS match score and actionable improvement roadmap."""

    # -------------------------------------------------------------------------
    # 1. Hard & Soft Skills Match
    # -------------------------------------------------------------------------
    resume_skill_names_lower = {s.name.lower() for s in resume.skills}

    # Build the full resume corpus — every piece of text the candidate wrote
    resume_full_text = " ".join(filter(None, [
        resume.summary,
        " ".join(s.name for s in resume.skills),
        " ".join(b.text for exp in resume.experience for b in exp.bullets),
        " ".join(p.description for p in resume.projects),
        " ".join(t for p in resume.projects for t in p.technologies),
        " ".join(exp.title for exp in resume.experience),
        " ".join(exp.company for exp in resume.experience),
    ])).lower()

    jd_required  = [s for s in jd.required_skills  if s.strip()]
    jd_preferred = [s for s in jd.preferred_skills if s.strip()]

    matched_skills   = []
    missing_required = []
    missing_preferred = []

    for req in jd_required:
        if _skill_present(req, resume_full_text, resume_skill_names_lower):
            matched_skills.append(req)
        else:
            missing_required.append(req)

    for pref in jd_preferred:
        if _skill_present(pref, resume_full_text, resume_skill_names_lower):
            matched_skills.append(pref)
        else:
            missing_preferred.append(pref)

    total_jd_skills = len(jd_required) + (len(jd_preferred) * 0.5)
    if total_jd_skills > 0:
        matched_weighted = (
            len([s for s in matched_skills if s in jd_required]) +
            len([s for s in matched_skills if s in jd_preferred]) * 0.5
        )
        keyword_coverage = min(matched_weighted / total_jd_skills, 1.0)
    else:
        # JD didn't list explicit tech skills → score based on responsibility overlap only
        keyword_coverage = 0.72

    # -------------------------------------------------------------------------
    # 2. Experience-level match
    # -------------------------------------------------------------------------
    candidate_years = 0.0
    today = date.today()
    for exp in resume.experience:
        start = exp.start_date
        end = exp.end_date or (today if exp.current or exp.start_date else None)

        if isinstance(start, str):
            try:
                start = datetime.strptime(start[:10], "%Y-%m-%d").date()
            except Exception:
                start = None
        if isinstance(end, str):
            try:
                end = datetime.strptime(end[:10], "%Y-%m-%d").date()
            except Exception:
                end = None

        if start and end and end >= start:
            candidate_years += (end - start).days / 365.25

    min_required_years = jd.min_years_experience or 1
    experience_match = min(candidate_years / min_required_years, 1.0) if min_required_years else 1.0

    # -------------------------------------------------------------------------
    # 3. Responsibility & Action Verb Alignment  (improved)
    # -------------------------------------------------------------------------
    all_bullets = [b.text for exp in resume.experience for b in exp.bullets]
    resume_bullets_text = " ".join(all_bullets).lower()

    _STOPWORDS = {
        "with","that","this","from","have","will","been","more","than",
        "they","their","were","also","into","over","such","your","work",
        "team","role","able","using","about","which","would","could","should",
        "must","need","make","take","give","when","where","what","help",
    }

    if jd.responsibilities:
        jd_resp_text = " ".join(r.lower() for r in jd.responsibilities)
        resp_kws  = {w for w in re.findall(r"\b[a-z]{4,}\b", jd_resp_text) if w not in _STOPWORDS}
        # Also add JD keywords_for_ats into the pool (boosts score when resume uses same verbs)
        resp_kws |= {w.lower() for w in jd.keywords_for_ats if len(w) >= 4}

        if resp_kws:
            matched_kw = sum(1 for kw in resp_kws if kw in resume_bullets_text or kw in resume_full_text)
            responsibility_similarity = min(matched_kw / len(resp_kws), 1.0)
        else:
            responsibility_similarity = 0.65
    else:
        responsibility_similarity = 0.65

    # -------------------------------------------------------------------------
    # 4. ATS Formatting & Structure Health Score
    # -------------------------------------------------------------------------
    format_points = 0.0
    # Contact info completeness (name, email, phone)
    if resume.contact.name: format_points += 0.25
    if resume.contact.email and "@" in resume.contact.email: format_points += 0.25
    if resume.contact.phone: format_points += 0.15
    if resume.summary and len(resume.summary) > 40: format_points += 0.15
    if len(resume.skills) >= 4: format_points += 0.10
    if len(resume.experience) >= 1 and len(all_bullets) >= 3: format_points += 0.10
    ats_formatting_score = min(format_points, 1.0)

    # -------------------------------------------------------------------------
    # 5. Impact Metrics & Quantification Score  (improved pattern coverage)
    # -------------------------------------------------------------------------
    metric_pattern = re.compile(
        r"(\d+\s*%"                          # percentages
        r"|\$\s*[\d,]+"                       # dollar amounts
        r"|\b\d+\s*(?:k|m|b|x|ms|sec|s|min|hrs?|days?|weeks?|months?|users?|customers?|"
        r"requests?|calls?|transactions?|records?|rows?|servers?|services?|pipelines?|"
        r"deployments?|teams?|engineers?|repos?|issues?|tickets?|clients?|projects?)\b"
        r"|\b\d{2,}\s+(?:percent|million|thousand|billion)\b"
        r"|\b(?:increased?|decreased?|reduced?|improved?|optimized?|scaled?|saved?|"
        r"boosted?|accelerated?|cut|grew|grew|tripled?|doubled?|halved?|achieved?|"
        r"delivered?|launched?|migrated?|automated?|eliminated?|streamlined?)\b"
        r")",
        re.I,
    )
    metric_bullets_count = sum(1 for b in all_bullets if metric_pattern.search(b))
    total_bullets        = max(len(all_bullets), 1)
    # Reward if ≥30 % of bullets have metrics (was 50 %)
    impact_metrics_score = min(metric_bullets_count / max(total_bullets * 0.30, 1.0), 1.0)

    # -------------------------------------------------------------------------
    # 6. Honest Weighted Overall ATS Score (0 - 100)
    # -------------------------------------------------------------------------
    # 35% Hard Skills, 25% Experience fit, 20% Responsibility similarity, 10% Impact metrics, 10% ATS formatting
    raw_score = (
        0.35 * keyword_coverage +
        0.25 * experience_match +
        0.20 * responsibility_similarity +
        0.10 * impact_metrics_score +
        0.10 * ats_formatting_score
    )
    overall_score = round(raw_score * 100, 1)

    # -------------------------------------------------------------------------
    # 7. Fit Verdict & Narrative
    # -------------------------------------------------------------------------
    if overall_score >= 80:
        fit_verdict = "Strong Fit (Ready for ATS Screening)"
        fit_summary = f"Candidate background demonstrates strong alignment with {jd.role_title}. Core required competencies ({', '.join(matched_skills[:5])}) are well established. Minor tailoring will ensure top percentile ATS ranking."
    elif overall_score >= 55:
        fit_verdict = "Moderate Fit (Tailoring Recommended)"
        fit_summary = f"Solid foundational experience for {jd.role_title}, but key skill and keyword gaps should be bridged. Reordering skills to emphasize target requirements and tailoring bullet points will significantly increase interview likelihood."
    else:
        fit_verdict = "Low Initial Fit (High Gap Identified)"
        fit_summary = f"Significant divergence in required technical skills and experience levels. Recommended to highlight transferable project milestones and incorporate missing JD domain keywords."

    # -------------------------------------------------------------------------
    # 8. Gaps, Suggestions, and High-Impact Improvements
    # -------------------------------------------------------------------------
    gaps: List[str] = []
    suggestions: List[str] = []
    high_impact_improvements: List[str] = []

    if missing_required:
        gaps.append(f"Missing required hard skills: {', '.join(missing_required)}")
        suggestions.append(f"Add direct or related experience for required tools: {', '.join(missing_required[:4])}")
        high_impact_improvements.append(f"Incorporate target skills '{', '.join(missing_required[:3])}' into Technical Skills & bullet achievements.")

    if missing_preferred:
        gaps.append(f"Missing preferred qualifications: {', '.join(missing_preferred)}")
        suggestions.append(f"Highlight any familiarity with preferred tech: {', '.join(missing_preferred[:3])}")

    if candidate_years < min_required_years:
        gaps.append(f"Experience duration ({candidate_years:.1f}y) is below stated JD minimum ({min_required_years}y)")
        suggestions.append("Emphasize high-complexity projects and accelerated leadership milestones to offset tenure gap.")
        high_impact_improvements.append("Highlight senior scope, architectural decisions, and production ownership in bullet points.")

    if impact_metrics_score < 0.6:
        gaps.append("Low metric density: Few bullet points contain quantified business impact or KPIs (%, $, latency, scale).")
        suggestions.append("Quantify results: rewrite bullets using 'Accomplished [X] as measured by [Y], by doing [Z]' format.")
        high_impact_improvements.append("Add measurable outcomes (e.g. 'reduced latency by 35%', 'handled 5M+ daily requests') to experience entries.")

    if not resume.summary:
        high_impact_improvements.append(f"Add a focused 2-sentence Professional Summary tailored to {jd.role_title}.")

    if not high_impact_improvements:
        high_impact_improvements.append("Align skill ordering to place top job posting keywords in the first visible row.")

    return MatchReport(
        overall_score=overall_score,
        keyword_coverage=round(keyword_coverage, 4),
        experience_match=round(experience_match, 4),
        responsibility_similarity=round(responsibility_similarity, 4),
        ats_formatting_score=round(ats_formatting_score, 4),
        impact_metrics_score=round(impact_metrics_score, 4),
        fit_verdict=fit_verdict,
        fit_summary=fit_summary,
        matched_skills=matched_skills[:20],
        missing_required_skills=missing_required[:10],
        missing_preferred_skills=missing_preferred[:10],
        gaps=gaps,
        suggestions=suggestions,
        high_impact_improvements=high_impact_improvements,
    )