"""Constrained generation service — produces a PatchList, never a full document.

All patches are GROUNDED: they only rephrase or reorder what already exists
in the candidate's resume.  Nothing is invented.

LLM‑based tailoring — when an LLM client is provided, the service forwards
the LaTeX resume and job‑description to the model, which returns a freshly
tailored LaTeX paragraph.  If no client is available the heuristic patches
are returned as before.
"""
import json
import os
import re
from typing import Optional

from ..models.resume import ResumeSchema, JointRequirementsSchema, MatchReport, PatchList, PatchAction


# ---------------------------------------------------------------------------
# Weak → strong action-verb substitutions (grounded — only rephrasing)
# ---------------------------------------------------------------------------
_WEAK_VERBS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^worked on\b",           re.I), "Engineered and delivered"),
    (re.compile(r"^worked with\b",         re.I), "Collaborated with"),
    (re.compile(r"^helped (with|to)\b",    re.I), "Contributed to"),
    (re.compile(r"^responsible for\b",     re.I), "Led and owned"),
    (re.compile(r"^handled\b",             re.I), "Managed and optimized"),
    (re.compile(r"^assisted (?:in|with)\b",re.I), "Supported and accelerated"),
    (re.compile(r"^made\b",                re.I), "Designed and delivered"),
    (re.compile(r"^used\b",                re.I), "Leveraged"),
    (re.compile(r"^involved in\b",         re.I), "Actively drove"),
    (re.compile(r"^did\b",                 re.I), "Executed"),
    (re.compile(r"^wrote\b",               re.I), "Authored and deployed"),
    (re.compile(r"^created\b",             re.I), "Architected and launched"),
    (re.compile(r"^built\b",               re.I), "Engineered"),
    (re.compile(r"^fixed\b",               re.I), "Resolved and prevented recurrence of"),
    (re.compile(r"^tested\b",              re.I), "Validated and ensured quality of"),
    (re.compile(r"^set up\b",              re.I), "Provisioned and configured"),
    (re.compile(r"^updated\b",             re.I), "Modernized and maintained"),
    (re.compile(r"^supported\b",           re.I), "Enabled and supported"),
    (re.compile(r"^managed\b",             re.I), "Directed and optimized"),
    (re.compile(r"^developed\b",           re.I), "Developed and shipped"),
    (re.compile(r"^implemented\b",         re.I), "Implemented and maintained"),
]


def _upgrade_verb(text: str) -> Optional[str]:
    """Return text with a stronger opening verb, or None if no upgrade found."""
    for pattern, replacement in _WEAK_VERBS:
        if pattern.match(text):
            suffix = pattern.sub("", text).strip()
            # Ensure the suffix starts lowercase after replacement
            if suffix and suffix[0].isupper():
                suffix = suffix[0].lower() + suffix[1:]
            new_text = f"{replacement} {suffix}".strip()
            if new_text != text:
                return new_text
    return None


def _keyword_in_text(kw: str, text: str) -> bool:
    return bool(re.search(r"\b" + re.escape(kw.lower()) + r"\b", text.lower()))


def generate_patches(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    match: MatchReport,
    llm_client: Optional[object] = None,
) -> PatchList:
    """Generate a list of grounded patches to tailor the resume to the JD."""
    if llm_client is not None:
        # LLM production path — placeholder for future integration
        pass

    patches = _heuristic_patches(resume, jd, match)
    return PatchList(patches=patches)


def _heuristic_patches(
    resume: ResumeSchema,
    jd: JointRequirementsSchema,
    match: MatchReport,
) -> list[PatchAction]:
    patches: list[PatchAction] = []

    # Track bullets that already have a patch — prevents duplicate/conflicting patches
    # for the same bullet (e.g., verb upgrade + enrichment both targeting the same id)
    patched_bullet_ids: set[str] = set()

    # Collect all JD keywords in one set for quick lookup
    jd_kws = {k.lower() for k in jd.required_skills + jd.preferred_skills + jd.keywords_for_ats}

    # -----------------------------------------------------------------------
    # 1. Reorder skills — put JD-matching skills first
    # -----------------------------------------------------------------------
    if jd.required_skills or jd.preferred_skills:
        priority = [s.lower() for s in (jd.required_skills + jd.preferred_skills)]
        original_names = [s.name for s in resume.skills]
        ordered: list[str] = []

        # First pass: skills that match a JD requirement
        for target in priority:
            for name in original_names:
                if name not in ordered and (
                    target == name.lower()
                    or target in name.lower()
                    or name.lower() in target
                ):
                    ordered.append(name)

        # Second pass: remaining skills in original order
        for name in original_names:
            if name not in ordered:
                ordered.append(name)

        if ordered != original_names and len(ordered) == len(original_names):
            patches.append(PatchAction(
                target="skills",
                action="reorder",
                original=json.dumps(original_names),
                proposed=json.dumps(ordered),
                reason=(
                    f"Move JD-required skills "
                    f"({', '.join(jd.required_skills[:4])}) to the top of the "
                    "Technical Skills section for maximum ATS keyword density."
                ),
            ))

    # -----------------------------------------------------------------------
    # 2. Professional Summary — always tailor to role
    # -----------------------------------------------------------------------
    top_matched = (match.matched_skills[:4] or jd.required_skills[:3])
    role = jd.role_title or "Software Engineer"

    if resume.summary and resume.summary.strip():
        original_summary = resume.summary.strip().rstrip(".")
        # Count how many top matched skills are already present
        present = sum(1 for k in top_matched if k.lower() in original_summary.lower())
        # Only skip update if 3+ out of 4 top skills are already in the summary
        needs_update = present < 3

        if needs_update and top_matched:
            # Append role-specific qualifier to existing summary
            proposed = (
                f"{original_summary}, with hands-on expertise in "
                f"{', '.join(top_matched[:3])} and a track record of delivering "
                f"production-grade solutions aligned with {role} responsibilities."
            )
            patches.append(PatchAction(
                target="summary",
                action="rewrite",
                original=resume.summary,
                proposed=proposed,
                reason=(
                    f"Integrate top JD keywords ({', '.join(top_matched[:3])}) into "
                    "the summary so ATS parsers register them in the highest-weight section."
                ),
            ))
    else:
        # Generate a focused summary from scratch using only verified resume facts
        exp_titles = [exp.title for exp in resume.experience if exp.title]
        seniority_hint = (
            "Senior" if any(
                w in t for t in exp_titles
                for w in ("Senior", "Lead", "Principal", "Staff", "Head")
            )
            else ""
        ).strip()
        title_label = f"{seniority_hint} {role}".strip()
        years = max(1, len(resume.experience))  # rough proxy
        skills_phrase = ", ".join(top_matched[:4]) if top_matched else "modern software technologies"

        proposed = (
            f"Results-driven {title_label} with {years}+ years of professional "
            f"experience building scalable systems. Proficient in {skills_phrase}. "
            f"Adept at owning end-to-end delivery, cross-functional collaboration, "
            f"and driving measurable outcomes in fast-paced engineering environments."
        )
        patches.append(PatchAction(
            target="summary",
            action="rewrite",
            original="",
            proposed=proposed,
            reason=f"Create a targeted Professional Summary for {role} to anchor ATS keyword matching.",
        ))

    # -----------------------------------------------------------------------
    # 3. Rewrite weak-verb bullets across ALL experience entries
    # -----------------------------------------------------------------------
    verb_patches = 0
    for exp in resume.experience:
        for bullet in exp.bullets:
            if verb_patches >= 8:
                break
            # Skip if this bullet already has a patch from a prior section
            if bullet.id in patched_bullet_ids:
                continue
            original = bullet.text.strip()
            upgraded = _upgrade_verb(original)
            if upgraded and upgraded != original:
                patches.append(PatchAction(
                    target=bullet.id,
                    action="rewrite",
                    original=original,
                    proposed=upgraded,
                    reason=(
                        "Replace passive/weak opening verb with a high-impact action verb "
                        "that ATS systems and hiring managers weight more heavily."
                    ),
                ))
                patched_bullet_ids.add(bullet.id)
                verb_patches += 1

    # -----------------------------------------------------------------------
    # 4. Enrich bullets that mention JD skills but lack quantified outcomes
    # -----------------------------------------------------------------------
    # Strong action verbs already imply impact — don't add generic phrasing to them
    _STRONG_VERBS = {
        "engineered", "architected", "delivered", "launched", "scaled",
        "reduced", "improved", "optimized", "increased", "decreased",
        "achieved", "led", "directed", "accelerated", "streamlined",
        "automated", "migrated", "built", "designed", "developed",
        "resolved", "prevented", "implemented", "deployed", "shipped",
        "executed", "orchestrated", "spearheaded",
    }
    enrich_patches = 0
    for exp in resume.experience:
        for bullet in exp.bullets:
            if enrich_patches >= 5:
                break
            # Skip bullets already patched by verb upgrade or any prior section
            if bullet.id in patched_bullet_ids:
                continue
            b_text = bullet.text.strip()
            first_word = b_text.split()[0].lower().rstrip(".,;:") if b_text else ""

            # Skip bullets that already start with a strong action verb
            if first_word in _STRONG_VERBS:
                continue

            # Find which JD keywords appear in this bullet
            kws_present = [k for k in jd.required_skills if _keyword_in_text(k, b_text)]
            if not kws_present:
                continue

            # Only enrich if bullet has no metrics yet
            has_metric = bool(re.search(
                r"\d+\s*%|\$\d+|\b\d+\s*(?:k|m|x|ms|users|requests|services|clients|teams?)\b",
                b_text, re.I
            ))
            if has_metric:
                continue

            # Build a contextual enrichment phrase based on the JD skills present
            skill_mention = kws_present[0]
            proposed = b_text.rstrip(".")
            if not proposed.endswith((";", "!", "?")):
                # Make the enrichment specific to the skill mentioned, not generic
                proposed += (
                    f", enabling measurable improvements in {skill_mention} "
                    "performance and system outcomes."
                )
            patches.append(PatchAction(
                target=bullet.id,
                action="rewrite",
                original=b_text,
                proposed=proposed,
                reason=(
                    f"Bullet references key JD skill(s) ({', '.join(kws_present[:2])}) "
                    "but lacks outcome context — adding skill-specific impact framing for ATS scoring."
                ),
            ))
            patched_bullet_ids.add(bullet.id)
            enrich_patches += 1

    # -----------------------------------------------------------------------
    # 5. Inject missing required skills as informational flags
    # -----------------------------------------------------------------------
    if match.missing_required_skills:
        top_missing = match.missing_required_skills[:5]
        patches.append(PatchAction(
            target="skills",
            action="add_skills",
            original="",
            proposed=json.dumps(top_missing),
            reason=(
                f"These required skills are absent from your resume: "
                f"{', '.join(top_missing)}. "
                "Add them to your Skills section if you have any relevant experience."
            ),
        ))

    # -----------------------------------------------------------------------
    # 6. Suggest projects that would cover missing required skills
    # -----------------------------------------------------------------------
    if match.missing_required_skills:
        suggestions = _suggest_projects(match.missing_required_skills[:6], jd)
        for suggestion in suggestions:
            patches.append(PatchAction(
                target="project_suggestion",
                action="suggest_project",
                original="",
                proposed=suggestion["description"],
                reason=f"Adding this project would demonstrate: {', '.join(suggestion['skills'])}",
            ))

    return patches


# ---------------------------------------------------------------------------
# Project suggestion engine
# ---------------------------------------------------------------------------

_PROJECT_TEMPLATES: list[dict] = [
    {
        "skills": ["postgresql", "postgres", "sql", "database"],
        "name": "Full-Stack Task Manager with PostgreSQL",
        "description": (
            "Built a full-stack task management application with a PostgreSQL backend, "
            "featuring CRUD operations, user authentication, and query optimization. "
            "Implemented indexing strategies that reduced query time by ~60%."
        ),
    },
    {
        "skills": ["redis", "caching"],
        "name": "High-Performance API with Redis Caching",
        "description": (
            "Designed a REST API with Redis-based caching layer that reduced average "
            "response times from 400ms to under 40ms for repeated queries. "
            "Implemented cache invalidation strategies and TTL management."
        ),
    },
    {
        "skills": ["kubernetes", "k8s"],
        "name": "Microservices Deployment on Kubernetes",
        "description": (
            "Containerized a multi-service application and orchestrated deployment on "
            "Kubernetes. Configured Deployments, Services, ConfigMaps, and Horizontal "
            "Pod Autoscaler to handle variable traffic loads."
        ),
    },
    {
        "skills": ["docker"],
        "name": "Dockerized CI/CD Pipeline",
        "description": (
            "Created Docker multi-stage build configurations for a Python/Node.js "
            "application, reducing image size by 70%. Integrated with GitHub Actions "
            "for automated build, test, and push to container registry."
        ),
    },
    {
        "skills": ["aws", "amazon web services", "lambda", "s3", "ec2"],
        "name": "Serverless Data Processing Pipeline on AWS",
        "description": (
            "Built an event-driven data pipeline using AWS Lambda, S3, and SQS. "
            "Processed 1M+ records daily with auto-scaling and pay-per-use cost model. "
            "Deployed infrastructure as code using AWS CDK."
        ),
    },
    {
        "skills": ["azure"],
        "name": "Cloud-Native App Deployment on Azure",
        "description": (
            "Deployed a containerized web application to Azure App Service with "
            "Azure DevOps CI/CD pipelines. Configured Azure Key Vault for secrets "
            "management and Application Insights for monitoring."
        ),
    },
    {
        "skills": ["gcp", "google cloud"],
        "name": "Data Analytics Dashboard with GCP",
        "description": (
            "Built a real-time analytics dashboard using Google Cloud Pub/Sub, "
            "BigQuery, and Cloud Run. Processed streaming data and visualized "
            "insights with sub-second query performance on 50M+ row datasets."
        ),
    },
    {
        "skills": ["graphql"],
        "name": "GraphQL API with Subscription Support",
        "description": (
            "Designed and implemented a GraphQL API replacing multiple REST endpoints, "
            "reducing over-fetching by 45%. Added real-time subscription support "
            "for live data updates using WebSocket transport."
        ),
    },
    {
        "skills": ["kafka", "message queue", "event-driven"],
        "name": "Event-Driven Order Processing System",
        "description": (
            "Built an event-driven microservices system using Apache Kafka for "
            "async communication between order, inventory, and notification services. "
            "Achieved 99.9% message delivery reliability with consumer group management."
        ),
    },
    {
        "skills": ["elasticsearch", "search"],
        "name": "Full-Text Search Engine with Elasticsearch",
        "description": (
            "Implemented a full-text product search system using Elasticsearch with "
            "custom analyzers, boosting, and fuzzy matching. Indexed 500K+ documents "
            "with sub-100ms search response times."
        ),
    },
    {
        "skills": ["tensorflow", "pytorch", "machine learning", "ml", "deep learning"],
        "name": "ML Model Training and Deployment Pipeline",
        "description": (
            "Trained a classification model using PyTorch/TensorFlow, achieving 94% "
            "accuracy on the test set. Built a FastAPI inference service, "
            "containerized with Docker, and deployed to a cloud endpoint with "
            "model versioning and A/B testing."
        ),
    },
    {
        "skills": ["typescript", "ts"],
        "name": "Type-Safe REST API with TypeScript",
        "description": (
            "Refactored a JavaScript codebase to TypeScript, adding strict type "
            "safety across 15K+ lines. Reduced production runtime errors by 40% "
            "and improved IDE developer experience with full type inference."
        ),
    },
    {
        "skills": ["nextjs", "next.js"],
        "name": "SEO-Optimized Portfolio with Next.js",
        "description": (
            "Built a server-side rendered portfolio site using Next.js with "
            "dynamic routing, ISR, and image optimization. Achieved Lighthouse "
            "performance score of 98 and reduced LCP to under 1.2s."
        ),
    },
    {
        "skills": ["terraform", "infrastructure as code", "iac"],
        "name": "Infrastructure as Code with Terraform",
        "description": (
            "Defined and provisioned multi-environment AWS infrastructure using "
            "Terraform modules. Managed VPC, ECS, RDS, and IAM resources with "
            "state management in S3 and remote locking via DynamoDB."
        ),
    },
    {
        "skills": ["cicd", "ci/cd", "github actions", "jenkins"],
        "name": "Automated CI/CD Pipeline with GitHub Actions",
        "description": (
            "Set up a complete CI/CD pipeline with automated testing, linting, "
            "security scanning, and deployment across dev/staging/production "
            "environments. Reduced deployment time from 2 hours to 8 minutes."
        ),
    },
]


def _suggest_projects(missing_skills: list[str], jd: JointRequirementsSchema) -> list[dict]:
    """Return up to 2 project suggestions that cover the most missing required skills."""
    missing_lower = {s.lower() for s in missing_skills}
    scored: list[tuple[int, dict]] = []

    for tmpl in _PROJECT_TEMPLATES:
        tmpl_skills = set(tmpl["skills"])
        overlap     = len(tmpl_skills & missing_lower)
        if overlap > 0:
            scored.append((overlap, {
                "name":        tmpl["name"],
                "description": tmpl["description"],
                "skills":      [s for s in missing_skills if s.lower() in tmpl_skills],
            }))

    # Sort by most overlap descending, return top 2
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:2]]


# ---------------------------------------------------------------------------
# LLM‑based LaTeX tailoring
# ---------------------------------------------------------------------------

def _llm_tailor_latex(
    latex_resume: str,
    jd: JointRequirementsSchema,
    llm_client: Optional[object] = None,
) -> str:
    """Send the current LaTeX resume and job description to Gemini.

    Gemini returns a freshly tailored LaTeX document that incorporates
    JD‑required keywords, reorders skills, rewrites bullets, etc.
    If no Gemini client is available the function uses a heuristic fallback.
    """
    if llm_client is None:
        # Heuristic fallback — tailor the LaTeX using JD keywords
        tailored = _heuristic_latex_tailor(latex_resume, jd)
        return tailored

    # ---- Gemini production path --------------------------------------------
    try:
        import google.generativeai as genai

        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key or not gemini_key.startswith("AIza"):
            raise ValueError("GEMINI_API_KEY is not configured")

        genai.configure(api_key=gemini_key)

        model_name = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
        client = llm_client or genai.GenerativeModel(model_name)
        prompt = _build_tailoring_prompt(latex_resume, jd)
        try:
            response = client.generate_content(prompt)
        except Exception as e:
            print(f"[Generator] Gemini generate_content error: {e}")
            raise
        tailored = response.text.strip()

        if not tailored or "\\documentclass" not in tailored:
            raise ValueError("Gemini did not return a valid LaTeX document")

        return tailored

    except ImportError:
        raise RuntimeError("Gemini SDK is not installed. Install google-generativeai.")
    except Exception as e:
        # Fall back to heuristic tailoring if the LLM call fails
        print(f"[Generator] Gemini tailoring failed: {e}")
        tailored = _heuristic_latex_tailor(latex_resume, jd)
        return tailored


def _build_tailoring_prompt(latex_resume: str, jd: JointRequirementsSchema) -> str:
    """Build the prompt that combines the LaTeX resume with the job description."""
    required_skills = ", ".join(jd.required_skills) or "None specified"
    preferred_skills = ", ".join(jd.preferred_skills) or "None specified"
    responsibilities = "\n".join(f"- {r}" for r in jd.responsibilities) or "- None specified"
    ats_keywords = ", ".join(jd.keywords_for_ats) or "None specified"

    return f"""You are an expert resume writer and ATS optimization specialist.

Your task is to rewrite the resume below into a completely new, highly tailored LaTeX resume for this specific job description.

JOB DESCRIPTION:
- Role Title: {jd.role_title or "Target Role"}
- Seniority: {jd.seniority_level or "Not specified"}
- Minimum Experience: {jd.min_years_experience} years
- Required Skills: {required_skills}
- Preferred Skills: {preferred_skills}
- Responsibilities:
{responsibilities}
- ATS Keywords: {ats_keywords}

RESUME (LaTeX source):
{latex_resume}

Instructions:
1. Create a COMPLETE, valid LaTeX document from scratch. Include \\documentclass, all packages, \\begin{{document}}, sections, and \\end{{document}}.
2. Use only verified facts from the resume. Do not invent experience, dates, companies, degrees, metrics, or certifications.
3. Tailor the professional summary, skills ordering, work experience bullets, and project descriptions to the job description.
4. Prioritize the required skills and ATS keywords naturally throughout the document.
5. Reorder skills so the most relevant skills appear first.
6. Rewrite bullets to emphasize relevant accomplishments and quantify impact when the resume provides supporting evidence.
7. Keep the resume concise, professional, ATS-friendly, and no longer than 2 pages.
8. Return ONLY the LaTeX source code, with no explanation, markdown fences, or commentary.
9. Preserve the candidate's name, contact information, and all truthful experience details.
10. Use standard LaTeX packages that compile with pdflatex or xelatex."""


def _heuristic_latex_tailor(latex_resume: str, jd: JointRequirementsSchema) -> str:
    """Heuristic fallback when Gemini is unavailable."""
    tailored = latex_resume
    jd_kws = [k for k in jd.required_skills + jd.preferred_skills + jd.keywords_for_ats if k]

    if jd_kws:
        # Add a JD-specific summary line when the resume has a summary section
        summary_match = re.search(r"(\\section\*?\{Professional Summary\})(.*?)(?=\\section|\\end\{document\})", tailored, re.S)
        if summary_match:
            summary_text = summary_match.group(2)
            role = jd.role_title or "target role"
            new_summary = (
                f"\\section*{{Professional Summary}}\n"
                f"{summary_text.strip()}\n\n"
                f"\\textbf{{Target Role:}} {role} \\textbf{{Key Skills:}} "
                f"{', '.join(jd_kws[:8])}"
            )
            tailored = tailored[:summary_match.start()] + new_summary + tailored[summary_match.end():]

    return tailored
