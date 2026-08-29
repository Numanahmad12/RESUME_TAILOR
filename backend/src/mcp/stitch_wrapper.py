"""Stitch MCP integration for enhanced resume parsing and analysis (stdlib-only stub)."""
import os
import re
from typing import Dict, Any, Optional


class StitchMCPWrapper:
    """Wrapper for Google Stitch MCP server operations.

    In production this calls the actual Stitch MCP server via its API.
    This implementation provides a stdlib-only fallback for local development.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("STITCH_API_KEY")
        self.base_url = "https://stitch.googleapis.com/v1"

    async def analyze_document_content(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Use Stitch to extract structured content from documents."""
        return await self._heuristic_parse(file_path, file_type)

    async def extract_entities(self, text: str, entity_types: list) -> Dict[str, Any]:
        """Extract entities (skills, companies, dates, etc.) from text."""
        return await self._heuristic_entity_extraction(text, entity_types)

    async def compare_documents(self, doc1_path: str, doc2_path: str) -> Dict[str, Any]:
        """Compare two documents and provide similarity analysis."""
        return await self._heuristic_comparison(doc1_path, doc2_path)

    # ------------------------------------------------------------------
    # Heuristic fallbacks (no external ML dependency)
    # ------------------------------------------------------------------

    async def _heuristic_parse(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Stdlib-based parsing fallback."""
        _SKILL_LIST = {
            "python", "java", "javascript", "react", "node", "aws", "docker",
            "kubernetes", "sql", "git", "linux", "agile", "scrum", "typescript",
            "angular", "vue", "django", "fastapi", "postgres", "redis", "kafka",
        }

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except OSError:
            text = file_path  # treat as raw text

        words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\+\#\.]{1,}\b", text.lower())
        skills = list({w for w in words if w in _SKILL_LIST})

        # Simple company heuristic: Title Case words near "at" / "@"
        companies = re.findall(r"\bat\s+([A-Z][A-Za-z\s&]{2,30})(?:\b|,)", text)

        # Dates: years in range 1990-2030
        dates = re.findall(r"\b(19[9]\d|20[0-3]\d)\b", text)

        return {
            "skills": skills[:20],
            "companies": list(set(companies))[:10],
            "dates": list(set(dates))[:10],
            "confidence": 0.65,
        }

    async def _heuristic_entity_extraction(self, text: str, entity_types: list) -> Dict[str, Any]:
        """Simple regex entity extraction."""
        extracted: Dict[str, Any] = {}

        for ent_type in entity_types:
            if ent_type == "SKILL":
                skills = re.findall(
                    r"\b(Python|JavaScript|TypeScript|Java|Go|React|Vue|Angular|"
                    r"AWS|Docker|Kubernetes|PostgreSQL|MongoDB|Redis|Kafka|SQL)\b", text
                )
                extracted[ent_type] = [{"text": s, "confidence": 0.8} for s in set(skills)]

            elif ent_type == "DATE":
                dates = re.findall(
                    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b"
                    r"|\b\d{4}\b", text
                )
                extracted[ent_type] = [{"text": d, "confidence": 0.9} for d in set(dates)]

            elif ent_type == "COMPANY":
                companies = re.findall(r"\bat\s+([A-Z][A-Za-z\s&]{2,30})\b", text)
                extracted[ent_type] = [{"text": c.strip(), "confidence": 0.7} for c in set(companies)]

            else:
                extracted[ent_type] = []

        return extracted

    async def _heuristic_comparison(self, doc1_path: str, doc2_path: str) -> Dict[str, Any]:
        """Word-overlap similarity between two text files."""
        try:
            with open(doc1_path, "r", encoding="utf-8", errors="ignore") as f:
                text1 = f.read().lower()
            with open(doc2_path, "r", encoding="utf-8", errors="ignore") as f:
                text2 = f.read().lower()
        except OSError:
            return {"similarity_score": 0.0, "common_entities": [], "differences": [], "confidence": 0.0}

        words1 = set(re.findall(r"\b[a-z]{3,}\b", text1))
        words2 = set(re.findall(r"\b[a-z]{3,}\b", text2))
        common = words1 & words2
        union = words1 | words2
        jaccard = len(common) / len(union) if union else 0.0

        return {
            "similarity_score": round(jaccard, 4),
            "common_entities": list(common)[:20],
            "differences": list((words1 - words2) | (words2 - words1))[:20],
            "confidence": 0.70,
        }