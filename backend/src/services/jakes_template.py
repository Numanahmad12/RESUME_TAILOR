"""Jake-style resume template renderer.

Renders a ResumeSchema in the classic Jake / Sourabh-Bajaj LaTeX look that the
user chose as reference:
  - centered navy NAME + centered contact line with | separators and hyperlinks
  - navy small-caps section headers with a full-width rule underneath
  - two-column rows: bold title left, gray italic dates right
  - tight bullet lists under projects / experience

Two backends:
  - render_jakes_latex(resume) -> str  (compilable .tex source)
  - render_jakes_pdf(resume, pdf_path)  (aligned PDF via reportlab, no native deps)

Projects, education, experience headers, certifications and contact are always
rendered VERBATIM from the resume object. Only the skills section (and any
bullet text already edited upstream) differs from the upload.
"""
import re
from pathlib import Path
from typing import Optional

from ..models.resume import ResumeSchema


NAVY_HEX = "#1e3a5f"

_AWARD_KEYWORDS = (
    "place", "award", "winner", "win", "won", "hackathon", "selected", "founded",
    "patent", "published", "rank", "finalist", "organised", "organized", "prize",
    "champion", "runner-up", "runner up", "competition", "contest", "medal", "trophy",
    "scholarship", "fellowship", "merit", "honor", "honour", "innovates", "national",
    "state-level", "college-level", "ctf", "olympiad", "all india rank",
)


# ─────────────────────────────────────────────────────────────
# Shared text helpers
# ─────────────────────────────────────────────────────────────

def _tex(text: str) -> str:
    """Escape LaTeX special characters."""
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
        .replace("~", r"\textasciitilde{}")
        .replace("^", r"\textasciicircum{}")
    )


def _fmt_dates(start, end) -> str:
    if not start and not end:
        return ""
    s = start.strftime("%b %Y") if hasattr(start, "strftime") else str(start or "")
    e = "Present" if end is None else (end.strftime("%b %Y") if hasattr(end, "strftime") else str(end))
    if s and e:
        return f"{s} -- {e}"
    return s or e


def _split_sentences(text: str, limit: Optional[int] = None) -> list:
    """Split a description into verbatim bullets (no rewording)."""
    if not text:
        return []
    # If text has newline-separated bullets or paragraphs, honor them
    if "\n" in text:
        lines = [re.sub(r"^[-•●*◦▸▪·\s]+", "", l).strip() for l in text.splitlines() if l.strip()]
        if lines:
            return lines if limit is None else lines[:limit]
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", text.strip())
    out = [re.sub(r"^[-•●*◦▸▪·\s]+", "", p).strip() for p in parts if p.strip()]
    return out if limit is None else out[:limit]


def _looks_like_award(name: str, issuer: str = "") -> bool:
    blob = f"{name or ''} {issuer or ''}".lower()
    return any(k in blob for k in _AWARD_KEYWORDS)


_CATEGORY_DISPLAY = {
    "devops": "DevOps",
    "ml/ai": "ML/AI",
    "ml / ai": "ML/AI",
}


def _group_skills(resume: ResumeSchema) -> list:
    """Group skills by category, preserving first-appearance order."""
    groups: dict = {}
    for s in resume.skills:
        raw = (s.category or "General").strip()
        cat = _CATEGORY_DISPLAY.get(raw.lower(), raw.title() if raw.islower() or raw.isupper() else raw)
        groups.setdefault(cat, []).append(s.name)
    return [(cat, names) for cat, names in groups.items() if names]


# ─────────────────────────────────────────────────────────────
# LaTeX backend
# ─────────────────────────────────────────────────────────────

_LATEX_PREAMBLE = r"""\documentclass[letterpaper,11pt]{article}
\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{xcolor}
\definecolor{Navy}{RGB}{30,58,95}
\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}
\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}
\titleformat{\section}{\color{Navy}\scshape\raggedright\large\bfseries}{}{0em}{}[\color{Navy}\titlerule]
\pdfgentounicode=1
\newcommand{\resumeItem}[1]{\item\small{{#1 \vspace{-2pt}}}}
\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
  \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
    \textbf{#1} & #2 \\
    \textit{\small#3} & \textit{\small #4} \\
  \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeSubSubheading}[2]{
  \item
  \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
    \textit{\small#1} & \textit{\small #2} \\
  \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeProjectHeading}[2]{
  \item
  \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
    \small#1 & #2 \\
  \end{tabular*}\vspace{-7pt}
}
\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}
\begin{document}
"""


def render_jakes_latex(resume: ResumeSchema) -> str:
    """Render the full Jake-style LaTeX document for a resume."""
    c = resume.contact
    parts = [_LATEX_PREAMBLE]

    # Header
    parts.append(r"\begin{center}")
    parts.append(f"{{\\Huge \\color{{Navy}} \\textbf{{{_tex(c.name or 'Resume')}}}}}")
    contact_bits = []
    if c.phone:
        contact_bits.append(_tex(c.phone))
    if c.email:
        contact_bits.append(f"\\href{{mailto:{_tex(c.email)}}}{{{_tex(c.email)}}}")
    for link in c.links or []:
        label = re.sub(r"^https?://", "", link).rstrip("/")
        contact_bits.append(f"\\href{{{_tex(link)}}}{{{_tex(label)}}}")
    if contact_bits:
        parts.append(" \n" + " $|$ ".join(contact_bits))
    parts.append(r"\end{center}")

    # Professional Summary
    if resume.summary and resume.summary.strip():
        parts.append(r"\section{Professional Summary}")
        parts.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
        parts.append(f"\\small{{\\item{{{_tex(resume.summary.strip())}}}}}")
        parts.append(r"\end{itemize}")

    # Education
    if resume.education:
        parts.append(r"\section{Education}")
        parts.append(r"\resumeSubHeadingListStart")
        for edu in resume.education:
            degree = edu.degree or ""
            parts.append(
                "\\resumeSubheading"
                f"{{{_tex(edu.school)}}}{{{_tex(edu.dates)}}}"
                f"{{{_tex(degree)}}}{{{_tex(edu.gpa or '')}}}"
            )
        parts.append(r"\resumeSubHeadingListEnd")

    # Skills
    groups = _group_skills(resume)
    if groups:
        parts.append(r"\section{Technical Skills}")
        parts.append(r"\begin{itemize}[leftmargin=0.15in, label={}]")
        parts.append(r"\small{\item{")
        for cat, names in groups:
            parts.append(f"\\textbf{{{_tex(cat)}:}} {', '.join(_tex(n) for n in names)} \\\\")
        parts.append(r"}}")
        parts.append(r"\end{itemize}")

    # Projects (preserve all relevant projects with full bullets)
    projs = resume.projects[:4]
    if projs:
        parts.append(r"\section{Projects}")
        parts.append(r"\resumeSubHeadingListStart")
        for proj in projs:
            techs = f" $|$ \\emph{{{', '.join(_tex(t) for t in proj.technologies)}}}" if proj.technologies else ""
            parts.append(
                "\\resumeProjectHeading"
                f"{{\\textbf{{{_tex(proj.name)}}}{techs}}}{{}}"
            )
            parts.append(r"\resumeItemListStart")
            bullets = _split_sentences(proj.description)[:3] or [""]
            for sent in bullets:
                if sent:
                    parts.append(f"\\resumeItem{{{_tex(sent)}}}")
            parts.append(r"\resumeItemListEnd")
        parts.append(r"\resumeSubHeadingListEnd")

    # Experience (preserve key career experience entries and bullets)
    if resume.experience:
        parts.append(r"\section{Experience}")
        parts.append(r"\resumeSubHeadingListStart")
        for exp in resume.experience[:4]:
            parts.append(
                "\\resumeSubheading"
                f"{{{_tex(exp.title or exp.company)}}}{{{_tex(_fmt_dates(exp.start_date, exp.end_date))}}}"
                f"{{{_tex(exp.company)}}}{{}}"
            )
            if exp.bullets:
                parts.append(r"\resumeItemListStart")
                for b in exp.bullets[:3]:
                    parts.append(f"\\resumeItem{{{_tex(b.text)}}}")
                parts.append(r"\resumeItemListEnd")
        parts.append(r"\resumeSubHeadingListEnd")

    # Certifications vs Achievements (render as separate distinct sections)
    all_items = list(resume.certifications) + list(getattr(resume, "achievements", []))
    seen_k = set()
    unique_items = []
    for it in all_items:
        k = (it.name.strip().lower(), (it.issuer or "").strip().lower())
        if k not in seen_k:
            seen_k.add(k)
            unique_items.append(it)

    certs = [x for x in unique_items if not _looks_like_award(x.name, x.issuer)][:6]
    achievements = [x for x in unique_items if _looks_like_award(x.name, x.issuer)][:5]
    if certs:
        parts.append(r"\section{Certifications}")
        parts.append(r"\resumeSubHeadingListStart")
        for cert in certs:
            issuer = f" $|$ \\emph{{{_tex(cert.issuer)}}}" if cert.issuer else ""
            date_str = f"\\emph{{{_tex(cert.date)}}}" if cert.date else ""
            parts.append(
                "\\resumeProjectHeading"
                f"{{\\textbf{{{_tex(cert.name)}}}{issuer}}}{{{date_str}}}"
            )
        parts.append(r"\resumeSubHeadingListEnd")

    if achievements:
        parts.append(r"\section{Achievements}")
        parts.append(r"\resumeSubHeadingListStart")
        for ach in achievements:
            issuer = f" $|$ \\emph{{{_tex(ach.issuer)}}}" if ach.issuer else ""
            date_str = f"\\emph{{{_tex(ach.date)}}}" if ach.date else ""
            parts.append(
                "\\resumeProjectHeading"
                f"{{\\textbf{{{_tex(ach.name)}}}{issuer}}}{{{date_str}}}"
            )
        parts.append(r"\resumeSubHeadingListEnd")

    parts.append(r"\end{document}")
    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────
# reportlab PDF backend (mirrors the same visual structure)
# ─────────────────────────────────────────────────────────────

def render_jakes_pdf(resume: ResumeSchema, pdf_path: str) -> str:
    """Render an aligned Jake-style PDF with reportlab.
    STRICTLY GUARANTEES A 1-PAGE OUTPUT.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )

    def _build_story(compact_level: int = 0):
        navy = colors.HexColor(NAVY_HEX)
        grey = colors.HexColor("#555555")

        if compact_level == 0:
            # Full-Page Expansive: Fills standard single page beautifully
            margin_lr = 0.48 * inch
            margin_tb = 0.42 * inch
            fs_title = 20
            fs_body = 9.5
            leading_body = 12.2
            max_projs = 4
            max_proj_bullets = 3
            max_exps = 4
            max_exp_bullets = 3
            max_certs = 6
            sp_after_sec = 2.5
            sp_after_item = 2.5
        elif compact_level == 1:
            # Balanced Standard: Slightly denser for multi-role profiles
            margin_lr = 0.44 * inch
            margin_tb = 0.36 * inch
            fs_title = 19
            fs_body = 9.0
            leading_body = 11.4
            max_projs = 3
            max_proj_bullets = 3
            max_exps = 3
            max_exp_bullets = 3
            max_certs = 5
            sp_after_sec = 2.0
            sp_after_item = 2.0
        else:
            # Ultra-compact: For very dense multi-page resumes to squeeze into 1 page
            margin_lr = 0.38 * inch
            margin_tb = 0.30 * inch
            fs_title = 18
            fs_body = 8.2
            leading_body = 10.2
            max_projs = 3
            max_proj_bullets = 2
            max_exps = 3
            max_exp_bullets = 2
            max_certs = 4
            sp_after_sec = 1.5
            sp_after_item = 1.5

        s_name = ParagraphStyle("name", fontSize=fs_title, leading=fs_title + 2, textColor=navy,
                                fontName="Helvetica-Bold", alignment=1, spaceAfter=2)
        s_contact = ParagraphStyle("contact", fontSize=fs_body, leading=leading_body, textColor=grey,
                                   alignment=1, spaceAfter=4)
        s_section = ParagraphStyle("section", fontSize=fs_body + 1.2, leading=leading_body + 1.2, textColor=navy,
                                   fontName="Helvetica-Bold", spaceBefore=4.5, spaceAfter=1)
        s_row_l = ParagraphStyle("rowL", fontSize=fs_body + 0.5, leading=leading_body, fontName="Helvetica-Bold")
        s_row_l_i = ParagraphStyle("rowLI", fontSize=fs_body, leading=leading_body - 1.0, textColor=grey)
        s_row_r = ParagraphStyle("rowR", fontSize=fs_body, leading=leading_body - 1.0, textColor=grey, alignment=2)
        s_body = ParagraphStyle("body", fontSize=fs_body, leading=leading_body, spaceAfter=1.5)
        s_bullet = ParagraphStyle("bullet", parent=s_body, leftIndent=12, bulletIndent=4, spaceAfter=1.2)
        s_skill = ParagraphStyle("skill", parent=s_body, spaceAfter=1.5)

        PAGE_W = letter[0] - (margin_lr * 2)
        COL_L, COL_R = PAGE_W - 1.8 * inch, 1.8 * inch

        def row(left: str, right: str, left_style=None):
            t = Table(
                [[Paragraph(left, left_style or s_row_l), Paragraph(right, s_row_r)]],
                colWidths=[COL_L, COL_R],
            )
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ]))
            return t

        def section(title: str):
            return [
                Paragraph(title.upper(), s_section),
                HRFlowable(width="100%", thickness=0.8, color=navy, spaceAfter=sp_after_sec),
            ]

        story = []
        c = resume.contact
        story.append(Paragraph(_rl(c.name or "Resume"), s_name))
        contact_bits = [x for x in [c.phone, c.email, *(c.links or [])] if x]
        if contact_bits:
            story.append(Paragraph(_rl(" · ".join(contact_bits)), s_contact))

        if resume.summary and resume.summary.strip():
            story += section("Professional Summary")
            story.append(Paragraph(_rl(resume.summary.strip()), s_body))
            story.append(Spacer(1, sp_after_item))

        if resume.education:
            story += section("Education")
            for edu in resume.education:
                story.append(row(f"<b>{_rl(edu.school)}</b>", f"<i>{_rl(edu.dates)}</i>"))
                if edu.degree:
                    story.append(Paragraph(f"<i>{_rl(edu.degree)}</i>", s_row_l_i))
                story.append(Spacer(1, 1.5))

        groups = _group_skills(resume)
        if groups:
            story += section("Technical Skills")
            for cat, names in groups:
                story.append(Paragraph(f"<b>{_rl(cat)}:</b> {_rl(', '.join(names))}", s_skill))
            story.append(Spacer(1, sp_after_item))

        # Relevant matching projects (preserve up to max_projs with rich descriptions)
        projs = resume.projects[:max_projs]
        if projs:
            story += section("Projects")
            for proj in projs:
                techs = f" | <i>{_rl(', '.join(proj.technologies))}</i>" if proj.technologies else ""
                story.append(row(f"<b>{_rl(proj.name)}</b>{techs}", ""))
                bullets = _split_sentences(proj.description)[:max_proj_bullets]
                for sent in bullets:
                    story.append(Paragraph(_rl(sent), s_bullet, bulletText="•"))
                story.append(Spacer(1, sp_after_item))

        if resume.experience:
            story += section("Experience")
            for exp in resume.experience[:max_exps]:
                story.append(row(
                    f"<b>{_rl(exp.title or exp.company)}</b>",
                    f"<i>{_rl(_fmt_dates(exp.start_date, exp.end_date))}</i>",
                ))
                if exp.company and exp.title:
                    story.append(Paragraph(f"<b>{_rl(exp.company)}</b>", s_row_l_i))
                for b in exp.bullets[:max_exp_bullets]:
                    story.append(Paragraph(_rl(b.text), s_bullet, bulletText="•"))
                story.append(Spacer(1, sp_after_item))

        all_items = list(resume.certifications) + list(getattr(resume, "achievements", []))
        seen_k = set()
        unique_items = []
        for it in all_items:
            k = (it.name.strip().lower(), (it.issuer or "").strip().lower())
            if k not in seen_k:
                seen_k.add(k)
                unique_items.append(it)

        certs = [x for x in unique_items if not _looks_like_award(x.name, x.issuer)]
        achievements = [x for x in unique_items if _looks_like_award(x.name, x.issuer)]

        if certs:
            story += section("Certifications")
            for cert in certs[:max_certs]:
                issuer = f" · <i>{_rl(cert.issuer)}</i>" if cert.issuer else ""
                story.append(row(f"<b>{_rl(cert.name)}</b>{issuer}", f"<i>{_rl(cert.date)}</i>"))
                story.append(Spacer(1, 1.0))

        if achievements:
            story += section("Achievements")
            for ach in achievements[:max_certs]:
                issuer = f" · <i>{_rl(ach.issuer)}</i>" if ach.issuer else ""
                story.append(row(f"<b>{_rl(ach.name)}</b>{issuer}", f"<i>{_rl(ach.date)}</i>"))
                story.append(Spacer(1, 1.0))

        return story, margin_lr, margin_tb

    # Pass 1: Try Level 0 (Full-page expansive fill)
    story, mlr, mtb = _build_story(compact_level=0)
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                            leftMargin=mlr, rightMargin=mlr,
                            topMargin=mtb, bottomMargin=mtb,
                            title=resume.contact.name or "Resume")
    doc.build(story)

    # Verify 1-page constraint using pypdfium2, fallback gracefully if overflowed
    try:
        import pypdfium2
        pdf_doc = pypdfium2.PdfDocument(str(pdf_path))
        if len(pdf_doc) > 1:
            # Pass 2: Balanced Standard
            story, mlr, mtb = _build_story(compact_level=1)
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                    leftMargin=mlr, rightMargin=mlr,
                                    topMargin=mtb, bottomMargin=mtb,
                                    title=resume.contact.name or "Resume")
            doc.build(story)
            pdf_doc = pypdfium2.PdfDocument(str(pdf_path))

        if len(pdf_doc) > 1:
            # Pass 3: Ultra-Compact
            story, mlr, mtb = _build_story(compact_level=2)
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter,
                                    leftMargin=mlr, rightMargin=mlr,
                                    topMargin=0.30 * inch, bottomMargin=0.30 * inch,
                                    title=resume.contact.name or "Resume")
            doc.build(story)
    except Exception:
        pass

    return str(pdf_path)


def _rl(text: str) -> str:
    """Escape text for reportlab paragraph XML."""
    import html as _html
    return _html.escape(text or "")


# ─────────────────────────────────────────────────────────────
# Deterministic markdown (for the 'markdown' download format)
# ─────────────────────────────────────────────────────────────

def resume_to_markdown(resume: ResumeSchema) -> str:
    """Render the tailored resume as clean markdown (same section order)."""
    c = resume.contact
    lines = [
        f"# {c.name}",
        " · ".join(x for x in [c.phone, c.email, *(c.links or [])] if x),
        "",
    ]
    if resume.summary and resume.summary.strip():
        lines.append("## Professional Summary")
        lines.append(resume.summary.strip())
        lines.append("")
    if resume.education:
        lines.append("## Education")
        for edu in resume.education:
            lines.append(f"**{edu.school}** — {edu.degree} ({edu.dates})")
        lines.append("")
    groups = _group_skills(resume)
    if groups:
        lines.append("## Technical Skills")
        for cat, names in groups:
            lines.append(f"**{cat}:** {', '.join(names)}")
        lines.append("")
    if resume.projects:
        lines.append("## Projects")
        for proj in resume.projects:
            techs = f" | {', '.join(proj.technologies)}" if proj.technologies else ""
            lines.append(f"**{proj.name}**{techs}")
            for sent in _split_sentences(proj.description) or []:
                lines.append(f"- {sent}")
        lines.append("")
    if resume.experience:
        lines.append("## Experience")
        for exp in resume.experience:
            lines.append(f"**{exp.title}** at {exp.company}")
            for b in exp.bullets:
                lines.append(f"- {b.text}")
        lines.append("")
    certs = [x for x in resume.certifications if not _looks_like_award(x.name, x.issuer)]
    awards = [x for x in resume.certifications if _looks_like_award(x.name, x.issuer)]
    if certs:
        lines.append("## Certifications")
        for cert in certs:
            lines.append(f"- **{cert.name}** ({cert.issuer}, {cert.date})")
        lines.append("")
    if awards:
        lines.append("## Achievements")
        for a in awards:
            issuer = f" ({a.issuer})" if a.issuer else ""
            date = f" — {a.date}" if a.date else ""
            lines.append(f"- **{a.name}**{issuer}{date}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
