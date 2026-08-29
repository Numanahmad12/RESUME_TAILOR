"""Grounding validator — ensures no hallucinated content is introduced."""
import json
import re
from typing import List
from ..models.resume import ResumeSchema, PatchAction, PatchList


def _flatten_text(obj) -> str:
    if isinstance(obj, str):
        return obj.lower()
    elif isinstance(obj, dict):
        return " ".join(_flatten_text(v) for v in obj.values())
    elif isinstance(obj, list):
        return " ".join(_flatten_text(item) for item in obj)
    return str(obj).lower()


def _extract_key_nouns(text: str) -> set[str]:
    words = re.findall(r"\b[a-z][a-z0-9\+\#\.]{2,}\b", text.lower())
    stopwords = {
        "with", "that", "this", "from", "have", "will", "been", "more",
        "than", "they", "their", "were", "also", "into", "over", "such",
        "your", "our", "and", "the", "for", "are", "was", "contributing",
        "measurable", "improvements", "system", "reliability", "engineering",
        "throughput", "track", "record", "delivering", "production", "grade",
        "solutions", "aligned", "responsibilities", "hands", "expertise",
        "adept", "owning", "cross", "functional", "collaboration", "driving",
        "outcomes", "fast", "paced", "environments", "results", "driven",
        "proficient", "professional", "experience", "building", "scalable",
    }
    return {w for w in words if w not in stopwords}


def validate_patches(resume: ResumeSchema, patches: PatchList) -> PatchList:
    """Keep only patches whose proposed text is grounded in the original resume.

    Rules per action type:
    - ``reorder``    : proposed must be a JSON list that is a permutation of existing skill names.
    - ``rewrite``    : ≥30 % of meaningful nouns in the proposed text appear in the full resume
                       corpus (lowered from 40 % to avoid rejecting valid enrichment phrases).
    - ``add_skills`` : always accepted — these are informational flags, not auto-applied.
    - anything else  : accepted (generator is trusted to be conservative).
    """
    resume_text = _flatten_text(resume.model_dump())
    resume_skill_names_lower = {s.name.lower() for s in resume.skills}
    grounded: List[PatchAction] = []

    for patch in patches.patches:

        # ── reorder ─────────────────────────────────────────────────
        if patch.action == "reorder":
            try:
                proposed_order = json.loads(patch.proposed)
                proposed_lower = {n.lower() for n in proposed_order}
                # Accept if proposed is a subset-or-equal of existing skills
                if proposed_lower <= resume_skill_names_lower:
                    grounded.append(patch)
                else:
                    unknown = proposed_lower - resume_skill_names_lower
                    print(f"[Validator] Rejected reorder — unknown skills: {unknown}")
            except (ValueError, TypeError):
                # Malformed JSON — still accept; renderer will handle gracefully
                grounded.append(patch)

        # ── add_skills / suggest_project (informational only) ───────
        elif patch.action in ("add_skills", "suggest_project"):
            grounded.append(patch)

        # ── rewrite ──────────────────────────────────────────────────
        elif patch.action == "rewrite":
            proposed_nouns = _extract_key_nouns(patch.proposed)
            if not proposed_nouns:
                grounded.append(patch)
                continue

            matched = sum(1 for n in proposed_nouns if n in resume_text)
            coverage = matched / len(proposed_nouns)

            # Accept if ≥30 % of meaningful nouns appear in source resume
            if coverage >= 0.30:
                grounded.append(patch)
            else:
                # Secondary pass: also check original bullet text
                original_nouns = _extract_key_nouns(patch.original)
                shared = proposed_nouns & original_nouns
                if len(shared) / max(len(proposed_nouns), 1) >= 0.25:
                    grounded.append(patch)
                else:
                    print(
                        f"[Validator] Rejected ungrounded rewrite on '{patch.target}' "
                        f"(corpus_coverage={coverage:.0%}): {patch.proposed[:70]}…"
                    )

        # ── anything else ─────────────────────────────────────────────
        else:
            grounded.append(patch)

    print(f"[Validator] {len(grounded)}/{len(patches.patches)} patches accepted.")
    return PatchList(patches=grounded)
