"""LaTeX generation service — produces grounded LaTeX from ResumeSchema.

All content is derived strictly from the parsed resume data — no hallucination,
no LLM generation.  The LaTeX template produces a clean, modern, one-page resume.
"""
from datetime import datetime
from typing import Optional

from ..models.resume import ResumeSchema


# ─────────────────────────────────────────────────────────────────────────────
# LaTeX template (modern resume class-style, no external dependencies)
# ─────────────────────────────────────────────────────────────────────────────

_LATEX_PREAMBLE = (
    r"\documentclass[11pt,letterpaper]{article}" + "\n"
    r"\usepackage[margin=0.65in]{geometry}" + "\n"
    r"\usepackage{array}" + "\n"
    r"\usepackage{calc}" + "\n"
    r"\usepackage{enumitem}" + "\n"
    r"\usepackage{hyperref}" + "\n"
    r"\usepackage{xcolor}" + "\n"
    r"\usepackage{sectfy}" + "\n"
    r"\sectionfont{\large\color{black}}" + "\n"
    r"\subsectionfont{\normalsize\bfseries\color{Navy}}" + "\n"
    r"\definecolor{Navy}{RGB}{30,58,95}" + "\n"
    r"\definecolor{DarkGrey}{RGB}{25,25,25}" + "\n"
    r"\definecolor{MutedGrey}{RGB}{100,100,100}" + "\n"
    r"\hypersetup{" + "\n"
    r"    pdfauthor={}," + "\n"
    r"    pdftitle={Resume}," + "\n"
    r"    colorlinks=false," + "\n"
    r"    urlcolor=Navy" + "\n"
    r"}" + "\n"
    r"\setlist[itemize]{noitemsep, topsep=0pt, leftmargin=*}" + "\n"
    r"\setlist[enumerate]{noitemsep, topsep=0pt, leftmargin=*}" + "\n"
    r"\begin{document}" + "\n"
    r"\thispagestyle{empty}" + "\n"
)

_LATEX_FOOTER = r"\end{document}"


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in a string."""
    if not text:
        return ""
    result = text
    result = result.replace("\\", r"\textbackslash{}")
    result = result.replace("&", r"\&")
    result = result.replace("%", r"\%")
    result = result.replace("$", r"\$")
    result = result.replace("#", r"\#")
    result = result.replace("_", r"\_")
    result = result.replace("{", r"\{")
    result = result.replace("}", r"\}")
    return result


def _format_date_range(start, end) -> str:
    """Format date range for LaTeX, e.g. 'Jan 2021 – Present'."""
    if not start and not end:
        return ""
    s = start.strftime("%b %Y") if hasattr(start, "strftime") else str(start or "")
    e = "Present" if end is None else (end.strftime("%b %Y") if hasattr(end, "strftime") else str(end))
    if s and e:
        return f"{s} – {e}"
    return s or e


def _to_latex(text: str) -> str:
    """Escape LaTeX special characters for use in document content."""
    if not text:
        return ""
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("&", r"\&")
        .replace("%", r"\%")
        .replace("$", r"\$")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("{", r"\{")
        .replace("}", r"\}")
    )


def _format_skills_latex(skills) -> str:
    """Format skills section for LaTeX, categorized."""
    if not skills:
        return ""
    cat_map = {}
    for s in skills:
        cat = (s.category or "General").title()
        cat_map.setdefault(cat, []).append(_to_latex(s.name))
    lines: list[str] = []
    for cat, names in cat_map.items():
        names_trimmed = names[:12]
        lines.append(f"{cat}: {', '.join(names_trimmed)}")
    items: list[str] = []
    for line in lines:
        items.append(r"\item " + line)
    return r"\begin{itemize}" + "\n".join(items) + r"\end{itemize}"


def _format_experience_latex(experience) -> str:
    """Format work experience section for LaTeX."""
    if not experience:
        return ""
    lines: list[str] = []
    for exp in experience:
        title = _to_latex(exp.title or "")
        company = _to_latex(exp.company or "")
        dates = _format_date_range(exp.start_date, exp.end_date)
        hdr_parts: list[str] = [title]
        if company:
            hdr_parts.append(f"at {company}")
        if dates:
            hdr_parts.append(dates)
        hdr = " ".join(hdr_parts)
        lines.append(r"\section*{" + hdr + "}")
        for b in exp.bullets:
            text = _to_latex(b.text)
            items: list[str] = [r"\item " + text]
            lines.append(r"\begin{itemize}")
            lines.extend(items)
            lines.append(r"\end{itemize}")
    return "".join(lines)


def _format_education_latex(education) -> str:
    """Format education section for LaTeX."""
    if not education:
        return ""
    lines: list[str] = []
    for edu in education:
        school = _to_latex(edu.school or "")
        degree = _to_latex(edu.degree or "")
        dates = _to_latex(edu.dates or "")
        parts: list[str] = [school]
        if degree:
            parts.append(degree)
        if dates:
            parts.append(f"({dates})")
        line = " ".join(parts)
        lines.append(r"\section*{" + line + "}")
    return "".join(lines)


def _format_projects_latex(projects) -> str:
    """Format projects section for LaTeX."""
    if not projects:
        return ""
    lines: list[str] = []
    for proj in projects:
        name = _to_latex(proj.name or "")
        desc = _to_latex(proj.description or "")
        techs = ", ".join(proj.technologies) if proj.technologies else ""
        lines.append(r"\subsection*{" + name + "}")
        if desc:
            lines.append("{" + desc + "}")
        if techs:
            lines.append(r"\textbf{Tech:}" + techs)
    return "".join(lines)


def _format_certifications_latex(certifications) -> str:
    """Format certifications section for LaTeX."""
    if not certifications:
        return ""
    lines: list[str] = []
    for cert in certifications:
        name = _to_latex(cert.name or "")
        issuer = _to_latex(cert.issuer or "")
        date_val = _to_latex(cert.date or "")
        parts: list[str] = [name]
        if issuer:
            parts.append(f"({issuer})")
        if date_val:
            parts.append(date_val)
        line = " ".join(parts)
        lines.append(r"\subsection*{" + line + "}")
    return "".join(lines)


def generate_latex(resume: ResumeSchema) -> str:
    """Generate a complete LaTeX document string from a ResumeSchema.

    The output is strictly grounded in the resume data — no hallucination,
    no artificial generation.  Caller is responsible for compiling (e.g.,
    xelatex, pdflatex) or saving the .tex file.
    """
    parts: list[str] = []

    parts.append(_LATEX_PREAMBLE)

    # Header: name and contact
    name = _to_latex(resume.contact.name or "Resume")
    parts.append(r"\begin{center}")
    parts.append(r"\large")
    parts.append(name)
    parts.append(r"\normalsize")
    parts.append(r"\end{center}")

    # Contact info
    contact_parts: list[str] = []
    if resume.contact.email:
        contact_parts.append(resume.contact.email)
    if resume.contact.phone:
        contact_parts.append(resume.contact.phone)
    contact_parts.extend(resume.contact.links or [])
    contact_str = " ".join(_to_latex(c) for c in contact_parts if c)
    if contact_str:
        parts.append(contact_str)
    parts.append("")  # blank line

    # Professional Summary
    if resume.summary and resume.summary.strip():
        parts.append(r"\section*{Professional Summary}")
        parts.append(resume.summary.strip())
        parts.append("")

    # Technical Skills
    if resume.skills:
        parts.append(r"\section*{Technical Skills}")
        parts.append(_format_skills_latex(resume.skills))
        parts.append("")

    # Work Experience
    if resume.experience:
        parts.append(r"\section*{Work Experience}")
        parts.append(_format_experience_latex(resume.experience))
        parts.append("")

    # Education
    if resume.education:
        parts.append(r"\section*{Education}")
        parts.append(_format_education_latex(resume.education))
        parts.append("")

    # Projects
    if resume.projects:
        parts.append(r"\section*{Projects}")
        parts.append(_format_projects_latex(resume.projects))
        parts.append("")

    # Certifications
    if resume.certifications:
        parts.append(r"\section*{Certifications}")
        parts.append(_format_certifications_latex(resume.certifications))
        parts.append("")

    parts.append(_LATEX_FOOTER)

    return "\n".join(parts)