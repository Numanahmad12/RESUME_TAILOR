"""PDF conversion service — converts LLM markdown output to PDF via WeasyPrint.

The pipeline: LLM returns markdown → convert to styled HTML → WeasyPrint → PDF.
Also provides LaTeX source output for users who want the .tex file.
"""
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Tuple

from ..services.latex_generator import generate_latex
from ..models.resume import (
    ResumeSchema, ContactInfo, Skill, ExperienceBullet,
    ExperienceEntry, EducationEntry, ProjectEntry, CertificationEntry,
)

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────────────────────
# Markdown → HTML
# ─────────────────────────────────────────────────────────────

def markdown_to_html(markdown_text: str, title: str = "Resume") -> str:
    """Convert markdown text to styled HTML for PDF rendering."""
    import markdown

    # Convert markdown to HTML
    extensions = ["tables", "fenced_code", "md_in_html"]
    html_body = markdown.markdown(markdown_text, extensions=extensions)

    # Clean up any remaining markdown artifacts
    html_body = _clean_html(html_body)

    # Wrap in styled HTML
    styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'Segoe UI', Calibri, Arial, sans-serif;
        margin: 0.65in 0.75in;
        color: #1a1a1a;
        font-size: 10pt;
        line-height: 1.45;
    }}
    h1 {{
        font-size: 22pt;
        color: #1e3a5f;
        margin-bottom: 2px;
        border-bottom: 2px solid #1e3a5f;
        padding-bottom: 6px;
    }}
    h2 {{
        font-size: 11pt;
        color: #1e3a5f;
        border-bottom: 1.2px solid #1e3a5f;
        padding-bottom: 2px;
        margin-top: 12px;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    h3 {{
        font-size: 10pt;
        color: #2c3e50;
        margin-top: 6px;
        margin-bottom: 2px;
    }}
    p {{ margin-bottom: 4px; }}
    ul {{ padding-left: 18px; margin-top: 2px; }}
    li {{ margin-bottom: 2px; }}
    strong {{ color: #1a1a1a; }}
    em {{ color: #555; }}
    .contact {{
        color: #555;
        font-size: 9pt;
        margin-bottom: 8px;
    }}
    .contact a {{
        color: #1e3a5f;
        text-decoration: none;
    }}
    .skills-section {{
        font-size: 9pt;
    }}
    .skills-section span {{
        display: inline-block;
        background: #eef2f7;
        border: 1px solid #d0d7e2;
        border-radius: 3px;
        padding: 1px 6px;
        margin: 1px 2px;
        font-size: 8.5pt;
    }}
    .skill-category {{
        font-weight: bold;
        color: #1e3a5f;
        margin-top: 4px;
        font-size: 9.5pt;
    }}
    .experience-entry {{
        margin-bottom: 8px;
    }}
    .experience-header {{
        font-weight: bold;
        font-size: 10pt;
    }}
    .experience-dates {{
        color: #666;
        font-size: 8.5pt;
        font-style: italic;
    }}
    .experience-bullets {{
        margin-left: 16px;
        font-size: 9pt;
    }}
    .education-entry {{
        margin-bottom: 2px;
    }}
    .project-entry {{
        margin-bottom: 6px;
    }}
    .project-tech {{
        color: #666;
        font-size: 8.5pt;
        font-style: italic;
    }}
    .cert-entry {{
        margin-bottom: 2px;
        font-size: 9pt;
    }}
    .section-divider {{
        border: none;
        border-top: 1px solid #e0e0e0;
        margin: 10px 0;
    }}
    .footer {{
        margin-top: 12px;
        font-size: 8pt;
        color: #999;
        text-align: center;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    return styled_html


def _clean_html(html: str) -> str:
    """Clean up any remaining markdown artifacts in HTML."""
    # Remove any raw markdown that didn't get converted
    html = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', html)
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    return html


# ─────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────

def markdown_to_pdf(markdown_text: str, output_name: Optional[str] = None) -> Tuple[str, str]:
    """Convert markdown text to PDF.

    Tries WeasyPrint first, then reportlab (pure Python), and finally falls
    back to saving styled HTML. Never raises — always returns a file path.
    Returns: (path, format) where format is 'pdf' or 'html'.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if output_name is None:
        output_name = f"rag_resume_{timestamp}"

    html = markdown_to_html(markdown_text, title=output_name)
    html_path = str(OUTPUT_DIR / f"{output_name}.html")
    pdf_path = str(OUTPUT_DIR / f"{output_name}.pdf")

    Path(html_path).write_text(html, encoding="utf-8")

    # Attempt 1: WeasyPrint (needs native Pango/Cairo libs — often missing on Windows)
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(target=pdf_path)
        return pdf_path, "pdf"
    except Exception as e:
        print(f"[PDF Converter] WeasyPrint failed ({e}); trying reportlab...")

    # Attempt 2: reportlab (pure Python, no system dependencies)
    try:
        _markdown_to_pdf_reportlab(markdown_text, pdf_path, title=output_name)
        return pdf_path, "pdf"
    except Exception as e:
        print(f"[PDF Converter] reportlab failed ({e}); falling back to HTML.")

    # Attempt 3: styled HTML the user can open/print to PDF from the browser
    return html_path, "html"


def _markdown_to_pdf_reportlab(markdown_text: str, pdf_path: str, title: str = "Resume") -> None:
    """Render markdown to PDF with reportlab platypus (no native deps)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    navy = colors.HexColor("#1e3a5f")
    styles = {
        "h1": ParagraphStyle("h1", fontSize=20, leading=24, textColor=navy,
                             spaceAfter=4, fontName="Helvetica-Bold"),
        "h2": ParagraphStyle("h2", fontSize=11, leading=14, textColor=navy,
                             fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "h3": ParagraphStyle("h3", fontSize=10, leading=13, textColor=colors.HexColor("#2c3e50"),
                             fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2),
        "body": ParagraphStyle("body", fontSize=9.5, leading=13.5, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", parent=None, fontSize=9.5, leading=13.5,
                                 leftIndent=18, bulletIndent=8, spaceAfter=2),
        "contact": ParagraphStyle("contact", fontSize=8.5, leading=11.5,
                                  textColor=colors.HexColor("#555555"), spaceAfter=6),
    }
    # fix parent reference (ParagraphStyle needs explicit parent, not None-dict)
    styles["bullet"] = ParagraphStyle("bullet", parent=styles["body"],
                                      leftIndent=18, bulletIndent=8, spaceAfter=2)

    story = []
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 0.06 * inch))
            continue
        rich = _md_inline_to_reportlab_xml(line)
        if line.startswith("### "):
            story.append(Paragraph(_md_inline_to_reportlab_xml(line[4:]), styles["h3"]))
        elif line.startswith("## "):
            story.append(Paragraph(_md_inline_to_reportlab_xml(line[3:]), styles["h2"]))
        elif line.startswith("# "):
            story.append(Paragraph(_md_inline_to_reportlab_xml(line[2:]), styles["h1"]))
        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            # Section header in **CONTACT** style
            text = line.strip("*").strip()
            if len(text.split()) <= 4:
                story.append(Paragraph(f"<b>{text}</b>", styles["h2"]))
            else:
                story.append(Paragraph(rich, styles["body"]))
        elif re.match(r"^[-*•]\s+", line):
            story.append(Paragraph(re.sub(r"^[-*•]\s+", "", rich), styles["bullet"], bulletText="•"))
        elif re.match(r"^\d+[.)]\s+", line):
            story.append(Paragraph(re.sub(r"^\d+[.)]\s+", "", rich), styles["bullet"], bulletText="•"))
        elif "@" in line or re.match(r"^[\d\s()+\-.]+$", line):
            story.append(Paragraph(rich, styles["contact"]))
        elif "|" in line and "---" not in line:
            story.append(Paragraph(rich.replace("|", " · "), styles["body"]))
        elif "---" in line:
            continue
        else:
            story.append(Paragraph(rich, styles["body"]))

    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                            leftMargin=0.7 * inch, rightMargin=0.7 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                            title=title)
    doc.build(story)


def _md_inline_to_reportlab_xml(text: str) -> str:
    """Convert **bold**, *italic*, `code` to reportlab paragraph XML (escaped)."""
    import html as _html
    text = _html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def markdown_to_latex(markdown_text: str, output_name: Optional[str] = None) -> Tuple[str, str]:
    """Convert markdown text to LaTeX source file.

    Returns: (tex_path, format) where format is 'latex'.
    Uses the grounded generator to create a proper LaTeX document.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if output_name is None:
        output_name = f"rag_resume_{timestamp}"

    tex_path = str(OUTPUT_DIR / f"{output_name}.tex")

    # Parse markdown back to structured text and generate LaTeX
    # For now, we generate LaTeX from the markdown content
    # In production, you'd parse markdown back into ResumeSchema
    latex_source = _markdown_to_latex_source(markdown_text)
    Path(tex_path).write_text(latex_source, encoding="utf-8")

    return tex_path, "latex"


def _markdown_to_latex_source(markdown_text: str) -> str:
    """Convert markdown resume to LaTeX source using the grounded generator."""
    # Parse markdown sections to extract data
    parsed = _parse_markdown_resume(markdown_text)

    # Build a ResumeSchema from parsed data
    resume = _build_resume_from_parsed(parsed)

    if resume:
        return generate_latex(resume)

    # Fallback: just wrap markdown in a LaTeX document
    return f"""\\documentclass[11pt,letterpaper]{{article}}
\\usepackage[margin=0.65in]{{geometry}}
\\usepackage{{enumitem}}
\\usepackage{{hyperref}}
\\begin{{document}}
\\thispagestyle{{empty}}
{markdown_text}
\\end{{document}}"""


def _parse_markdown_resume(markdown_text: str) -> dict:
    """Parse markdown resume into structured data."""
    sections = {}
    current_section = None
    current_content = []

    for line in markdown_text.splitlines():
        stripped = line.strip()
        # Detect section headers
        if re.match(r'^\*\*[A-Z][A-Z\s]+\*\*$', stripped) or re.match(r'^##\s+[A-Z]', stripped):
            if current_section:
                sections[current_section] = "\n".join(current_content)
            current_section = re.sub(r'^\*\*|^\*\*$|^\#\#\s+', '', stripped).strip().lower()
            current_content = []
        else:
            current_content.append(stripped)

    if current_section:
        sections[current_section] = "\n".join(current_content)

    return sections


def _build_resume_from_parsed(sections: dict) -> Optional[ResumeSchema]:
    """Build ResumeSchema from parsed markdown sections."""
    try:
        contact = ContactInfo(name="", email="", phone="", links=[])
        skills = []
        experience = []
        education = []
        projects = []
        certifications = []
        summary = ""

        # Parse summary
        if "professional summary" in sections:
            summary = sections["professional summary"].strip()

        # Parse skills
        if "technical skills" in sections:
            skill_text = sections["technical skills"]
            # Extract skill names from text like "Language: Python, JavaScript"
            for line in skill_text.split("\n"):
                line = line.strip()
                if not line or line.startswith("**"):
                    continue
                parts = re.split(r"[:,]", line)
                for part in parts:
                    part = part.strip()
                    if part and len(part) > 2 and len(part) < 40:
                        skills.append(Skill(name=part, category="General"))

        # Parse experience
        if "work experience" in sections:
            exp_text = sections["work experience"]
            # Simple parsing of company/title blocks
            current_exp = None
            for line in exp_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if re.match(r'^\*', line):
                    # Bullet point
                    if current_exp:
                        current_exp["bullets"].append(ExperienceBullet(id=f"exp_{len(experience)+1}.b{len(current_exp['bullets'])}", text=line.lstrip("* ").strip()))
                elif re.search(r'\d{4}', line) and not line.startswith("-"):
                    # New entry with date
                    if current_exp:
                        experience.append(ExperienceEntry(**current_exp))
                    current_exp = {
                        "id": f"exp_{len(experience)+1}",
                        "company": "",
                        "title": line.split("(")[0].strip(),
                        "start_date": None,
                        "end_date": None,
                        "current": False,
                        "bullets": [],
                    }
                elif current_exp and not current_exp["title"]:
                    current_exp["title"] = line

            if current_exp:
                experience.append(ExperienceEntry(**current_exp))

        # Parse education
        if "education" in sections:
            edu_text = sections["education"]
            for line in edu_text.split("\n"):
                line = line.strip()
                if line and not line.startswith("-"):
                    education.append(EducationEntry(school=line, degree="", dates="", gpa=None))

        # Parse projects
        if "projects" in sections:
            proj_text = sections["projects"]
            for line in proj_text.split("\n"):
                line = line.strip()
                if line and not line.startswith("-"):
                    projects.append(ProjectEntry(name=line, description="", technologies=[], url=""))

        return ResumeSchema(
            contact=contact, summary=summary, skills=skills,
            experience=experience, education=education,
            projects=projects, certifications=certifications,
        )
    except Exception as e:
        print(f"[PDF Converter] Failed to parse markdown to ResumeSchema: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────

def _fmt_dates(start, end) -> str:
    if not start and not end:
        return ""
    s = start.strftime("%b %Y") if hasattr(start, "strftime") else str(start or "")
    e = "Present" if end is None else (end.strftime("%b %Y") if hasattr(end, "strftime") else str(end))
    return f"{s} – {e}" if s and e else s or e
