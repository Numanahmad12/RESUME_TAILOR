#!/usr/bin/env python3
"""Generate docs/architecture.mmd — Mermaid diagram of the Resume Builder pipeline.

Run: python scripts/generate_graph.py
"""
from pathlib import Path
import json

REPO_ROOT = Path(__file__).parent.parent
INDEX_PATH = REPO_ROOT / "project_index.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "architecture.mmd"

DIAGRAM = """\
flowchart TD
    subgraph Client["🌐 Next.js Frontend"]
        U[Upload Resume + JD]
        A[Analyze & Score]
        R[Review Patches]
        D[Download Tailored Resume]
    end

    subgraph API["⚡ FastAPI Backend"]
        EP1[POST /api/upload/resume]
        EP2[POST /api/upload/jd]
        EP3[POST /api/analyze]
        EP4[POST /api/generate]
        EP5[POST /api/apply]
        EP6[POST /api/render/pdf]
        EP7[POST /api/render/docx]
    end

    subgraph Pipeline["🔄 Pipeline Stages"]
        P1["① Ingestion & Parsing<br/>pdfplumber / python-docx"]
        P2["② JD Analysis<br/>regex + keyword extraction"]
        P3["③ Gap & Match Analysis<br/>keyword + experience + similarity"]
        P4["④ Constrained Generation<br/>patch list (never full rewrite)"]
        P5["⑤ Grounding Validator<br/>hallucination guardrail"]
        P6["⑥ Human-in-Loop Review<br/>accept / reject / edit patches"]
        P7["⑦ Rendering<br/>DOCX (docxtpl) / PDF (weasyprint)"]
    end

    subgraph Schema["📐 Common Schema"]
        S1[ResumeSchema]
        S2[JointRequirementsSchema]
        S3[MatchReport]
        S4[PatchList]
    end

    U --> EP1 & EP2
    EP1 --> P1 --> S1
    EP2 --> P2 --> S2
    A --> EP3 --> P3 --> S3
    P3 --> EP4 --> P4 --> P5 --> S4
    R --> EP5 --> P6
    D --> EP6 & EP7 --> P7

    S1 & S2 --> P3
    S3 & S1 & S2 --> P4

    classDef frontend fill:#4f46e5,stroke:#6366f1,color:#fff
    classDef api fill:#1e3a5f,stroke:#3b82f6,color:#fff
    classDef pipeline fill:#065f46,stroke:#10b981,color:#fff
    classDef schema fill:#78350f,stroke:#f59e0b,color:#fff

    class U,A,R,D frontend
    class EP1,EP2,EP3,EP4,EP5,EP6,EP7 api
    class P1,P2,P3,P4,P5,P6,P7 pipeline
    class S1,S2,S3,S4 schema
"""


def main() -> None:
    output_dir = OUTPUT_PATH.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(DIAGRAM, encoding="utf-8")
    print(f"[OK] Architecture diagram written to: {OUTPUT_PATH}")

    # Also print project index summary
    if INDEX_PATH.exists():
        index = json.loads(INDEX_PATH.read_text())
        print(f"\nProject: {index.get('project')} v{index.get('version')}")
        for pkg, info in index.get("packages", {}).items():
            print(f"  {pkg}: {info.get('path')}")


if __name__ == "__main__":
    main()
