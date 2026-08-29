import sys
sys.path.insert(0, '.')
import fitz
from common.schema.resume import (
    ResumeSchema, ContactInfo, Skill, ExperienceEntry,
    ExperienceBullet, EducationEntry, ProjectEntry, CertificationEntry
)


def generate_pdf_pymupdf(resume: ResumeSchema, output_path: str) -> str:
    """Generate a clean, professional ATS-friendly PDF using PyMuPDF."""
    doc = fitz.open()

    PAGE_WIDTH = 612   # 8.5 x 72
    PAGE_HEIGHT = 792  # 11.0 x 72
    MARGIN_LEFT = 54   # 0.75 in
    MARGIN_RIGHT = 54
    MARGIN_TOP = 50
    MARGIN_BOTTOM = 50
    CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

    page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
    y = MARGIN_TOP

    def check_page_break(needed_height: float):
        nonlocal page, y
        if y + needed_height > PAGE_HEIGHT - MARGIN_BOTTOM:
            page = doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
            y = MARGIN_TOP

    def draw_text_line(text: str, fontsize: float = 10, fontname: str = "helv", color=(0.1, 0.1, 0.1), bold: bool = False, x: float = MARGIN_LEFT):
        nonlocal y
        check_page_break(fontsize + 4)
        fname = "hebo" if bold else fontname
        page.insert_text((x, y + fontsize), text, fontsize=fontsize, fontname=fname, color=color)
        y += fontsize + 4

    def draw_wrapped_paragraph(text: str, fontsize: float = 9.5, fontname: str = "helv", color=(0.15, 0.15, 0.15), indent: float = 0):
        nonlocal y
        if not text:
            return
        # Calculate chars per line roughly
        x = MARGIN_LEFT + indent
        max_w = CONTENT_WIDTH - indent
        words = text.split()
        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            # Estimate width using fitz get_text_length
            w = fitz.get_text_length(test_line, fontname=fontname, fontsize=fontsize)
            if w <= max_w:
                line = test_line
            else:
                if line:
                    check_page_break(fontsize + 3)
                    page.insert_text((x, y + fontsize), line, fontsize=fontsize, fontname=fontname, color=color)
                    y += fontsize + 3
                line = word
        if line:
            check_page_break(fontsize + 3)
            page.insert_text((x, y + fontsize), line, fontsize=fontsize, fontname=fontname, color=color)
            y += fontsize + 3

    def draw_section_heading(title: str):
        nonlocal y
        check_page_break(28)
        y += 8
        page.insert_text((MARGIN_LEFT, y + 11), title.upper(), fontsize=11, fontname="hebo", color=(0.12, 0.23, 0.37))
        y += 15
        # Draw divider line
        page.draw_line((MARGIN_LEFT, y), (PAGE_WIDTH - MARGIN_RIGHT, y), color=(0.12, 0.23, 0.37), width=1.0)
        y += 6

    # 1. Header: Name
    name = resume.contact.name or "Candidate Resume"
    check_page_break(32)
    page.insert_text((MARGIN_LEFT, y + 18), name, fontsize=20, fontname="hebo", color=(0.12, 0.23, 0.37))
    y += 24

    # 2. Contact details
    contact_parts = []
    if resume.contact.email:
        contact_parts.append(resume.contact.email)
    if resume.contact.phone:
        contact_parts.append(resume.contact.phone)
    if resume.contact.links:
        contact_parts.extend(resume.contact.links)
    contact_line = "  |  ".join(contact_parts)
    if contact_line:
        draw_text_line(contact_line, fontsize=9, fontname="helv", color=(0.4, 0.4, 0.4))
        y += 4

    # 3. Summary
    if resume.summary:
        draw_section_heading("Professional Summary")
        draw_wrapped_paragraph(resume.summary, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))
        y += 2

    # 4. Skills
    if resume.skills:
        draw_section_heading("Technical Skills")
        # Group by category if available
        cat_map = {}
        for s in resume.skills:
            cat_map.setdefault(s.category.title(), []).append(s.name)
        for cat, skill_names in cat_map.items():
            line = f"{cat}: " + ", ".join(skill_names)
            draw_wrapped_paragraph(line, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2), indent=0)
        y += 2

    # 5. Experience
    if resume.experience:
        draw_section_heading("Work Experience")
        for exp in resume.experience:
            check_page_break(24)
            # Company and Title
            header = f"{exp.title}"
            if exp.company:
                header += f"  —  {exp.company}"
            dates = ""
            if exp.start_date:
                s = exp.start_date.strftime("%b %Y") if hasattr(exp.start_date, 'strftime') else str(exp.start_date)
                e = "Present" if exp.current or not exp.end_date else (exp.end_date.strftime("%b %Y") if hasattr(exp.end_date, 'strftime') else str(exp.end_date))
                dates = f"{s} – {e}"

            # Draw title line
            page.insert_text((MARGIN_LEFT, y + 10), header, fontsize=10.5, fontname="hebo", color=(0.15, 0.15, 0.15))
            if dates:
                w = fitz.get_text_length(dates, fontname="helv", fontsize=9)
                page.insert_text((PAGE_WIDTH - MARGIN_RIGHT - w, y + 9), dates, fontsize=9, fontname="helv", color=(0.45, 0.45, 0.45))
            y += 14

            # Bullets
            for bullet in exp.bullets:
                bullet_text = f"•  {bullet.text}"
                draw_wrapped_paragraph(bullet_text, fontsize=9.5, fontname="helv", color=(0.25, 0.25, 0.25), indent=10)
            y += 4

    # 6. Education
    if resume.education:
        draw_section_heading("Education")
        for edu in resume.education:
            check_page_break(18)
            edu_line = edu.school
            if edu.degree:
                edu_line += f"  —  {edu.degree}"
            if edu.dates:
                edu_line += f" ({edu.dates})"
            draw_text_line(edu_line, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2))

    # 7. Projects
    if resume.projects:
        draw_section_heading("Projects")
        for proj in resume.projects:
            check_page_break(20)
            draw_text_line(proj.name, fontsize=10, bold=True, color=(0.15, 0.15, 0.15))
            if proj.description:
                draw_wrapped_paragraph(proj.description, fontsize=9.5, fontname="helv", color=(0.25, 0.25, 0.25), indent=8)
            if proj.technologies:
                tech_line = "Technologies: " + ", ".join(proj.technologies)
                draw_text_line(tech_line, fontsize=8.5, fontname="helv", color=(0.45, 0.45, 0.45), indent=8)
            y += 2

    # 8. Certifications
    if resume.certifications:
        draw_section_heading("Certifications")
        for cert in resume.certifications:
            check_page_break(16)
            cert_line = f"•  {cert.name}"
            if cert.issuer:
                cert_line += f"  —  {cert.issuer}"
            if cert.date:
                cert_line += f" ({cert.date})"
            draw_text_line(cert_line, fontsize=9.5, fontname="helv", color=(0.2, 0.2, 0.2), indent=6)

    doc.save(output_path)
    doc.close()
    return output_path


# Test generation
sample_res = ResumeSchema(
    contact=ContactInfo(name="Jane Developer", email="jane@example.com", phone="(555) 000-1111", links=["linkedin.com/in/janedev"]),
    summary="Passionate Senior Software Engineer with 7+ years developing scalable distributed systems.",
    skills=[Skill(name="Python", category="Language"), Skill(name="TypeScript", category="Language"), Skill(name="AWS", category="DevOps"), Skill(name="PostgreSQL", category="Database")],
    experience=[
        ExperienceEntry(
            id="exp_1", company="Tech Corp", title="Lead Engineer", current=True,
            bullets=[
                ExperienceBullet(id="exp_1.b1", text="Architected FastAPI microservices handling 50k requests/sec with Redis caching."),
                ExperienceBullet(id="exp_1.b2", text="Streamlined deployment pipelines using Docker, Kubernetes, and GitHub Actions."),
            ]
        )
    ],
    education=[EducationEntry(school="MIT", degree="B.S. Computer Science", dates="2017")]
)

generate_pdf_pymupdf(sample_res, "test_render.pdf")
print("PyMuPDF PDF generated successfully!")
with open("test_render.pdf", "rb") as f:
    header = f.read(10)
    print("Header bytes:", header)
    assert header.startswith(b"%PDF-")
print("Verified genuine PDF binary output!")
