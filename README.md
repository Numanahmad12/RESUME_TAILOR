# ResumeAI — AI-Powered ATS Resume Tailoring Engine

[![Vercel Deployment](https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://resume-tailor-eta-nine.vercel.app)
[![Render Backend](https://img.shields.io/badge/Render-API%20Live-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://resume-tailor-vdyx.onrender.com)
[![Next.js](https://img.shields.io/badge/Next.js%2014-black?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python%203.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Three.js](https://img.shields.io/badge/Three.js-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
[![GSAP](https://img.shields.io/badge/GSAP-ScrollTrigger-88CE02?style=for-the-badge&logo=greensock&logoColor=white)](https://greensock.com/gsap/)

> **Grounded, ATS-Optimized, Single-Page Resume Tailoring Engine with an Interactive 3D WebGL Experience.**

---

## 🌐 Live Production Links

- 🚀 **Live Web Application (Vercel)**: [**https://resume-tailor-eta-nine.vercel.app**](https://resume-tailor-eta-nine.vercel.app)
- ⚙️ **Production API (Render)**: [**https://resume-tailor-vdyx.onrender.com**](https://resume-tailor-vdyx.onrender.com)
- 📂 **GitHub Repository**: [**https://github.com/Numanahmad12/RESUME_TAILOR**](https://github.com/Numanahmad12/RESUME_TAILOR)

---

## ⚡ Key Highlights & Features

### 1. 🌟 Interactive 3D Resume Hero (Three.js + GSAP)
- **High-Fidelity 3D Resume Document**: Modeled in WebGL (`@react-three/fiber` + Three.js) with metallic bevels, glassmorphic depth, and crisp typography.
- **Dynamic AI Laser Scanner**: An energetic laser beam continuously scans down the document, simulating real-time ATS keyword evaluation.
- **Orbiting 3D Metric Badges**: Floating parallax chips displaying `98% ATS Match`, `National Finalist · AIR 21`, and `Grounded RAG Pipeline`.
- **Mouse Tilt Physics**: Damped lerp orientation following the visitor's cursor with holographic specular sheen.
- **GSAP ScrollTrigger**: Smoothly elevates, rotates, and expands into the page as the user scrolls.

### 2. 🏆 Separate Achievements & Certifications
- **Intelligent Classification**: Automatically distinguishes national competitions, hackathons, awards, and rankings from courses and certifications.
- **Distinct Layout Sections**: Jake's Resume PDF and LaTeX templates render independent headers with navy rules:
  - **`CERTIFICATIONS`**: Coursework, professional licenses (Coursera, DeepLearning.AI, OpenCV).
  - **`ACHIEVEMENTS`**: Hackathons, competition honors, national ranks (e.g. *Robocon AIR 21*, *India Innovates National Finalist*).
- **Dedicated Frontend Review Cards**: Step 4 features separate review and editing modules.

### 3. 📄 Strict 1-Page Layout with Full Vertical Coverage
- **Adaptive Multi-Pass Layout Engine**:
  - **Level 0 (Expansive Fill)**: 9.5pt body / 10pt headers, 12.2pt leading, 0.42in margins. Eliminates the bottom half-empty page issue.
  - **Level 1 & 2 (Balanced / Compact Fallbacks)**: Dynamically tightens line height only when content overflows, strictly maintaining a 1-page fit.
- Preserves all relevant projects, quantified bullet points, and verified credentials.

### 4. 🔍 6-Dimension Actionable Gap Engine
- Diagnoses gaps between candidate background and Job Description across 6 key dimensions:
  1. **Hard Skills Gap** (High Priority)
  2. **Preferred Skills Gap** (Medium Priority)
  3. **Experience Tenure Gap** (Scope re-framing)
  4. **Impact Metrics & Quantification** (Data/Metric additions)
  5. **Domain & Architecture Breadth**
  6. **Industry Certifications**
- Provides actionable, step-by-step guidance on how to bridge each gap.

### 5. 🛡️ Zero-Hallucination RAG Grounding
- Embeds verified facts using `sentence-transformers` vector embeddings.
- Guarantees factual integrity: never fabricates companies, degrees, dates, or contact info.

### 6. 📦 Multi-Format Production Exports
- **PDF**: Jake's Resume ReportLab engine with crisp typography and single-page constraint verification.
- **LaTeX**: Clean, ATS-friendly `resume.tex` code ready for Overleaf.
- **DOCX**: Word-compatible formatted resume document.
- **Markdown**: Clean, portable text version.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────┐
                                  │   Next.js 14 Frontend  │
                                  │   (Vercel Production)  │
                                  └───────────┬────────────┘
                                              │
                         REST API Proxies (/api/export, /api/tailor)
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │   FastAPI Cloud Backend│
                                  │   (Render Production)  │
                                  └───────────┬────────────┘
                                              │
             ┌────────────────────────────────┼────────────────────────────────┐
             │                                │                                │
             ▼                                ▼                                ▼
  ┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐
  │ Resume & JD Parser   │        │ RAG & Gap Analyzer   │        │  Multi-Format Render │
  │ • PDFPlumber / Fitz  │        │ • Sentence-Embeddings│        │  • ReportLab (Jake's)│
  │ • Smart Award Filter │        │ • Google Gemini LLM  │        │  • LaTeX Generator   │
  │ • DOCX Extractor     │        │ • Anti-Hallucination │        │  • DOCX & Markdown   │
  └──────────────────────┘        └──────────────────────┘        └──────────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | Next.js 14, React 18, Tailwind CSS, TypeScript, Framer Motion |
| **3D & Animation** | Three.js, `@react-three/fiber`, `@react-three/drei`, GSAP, ScrollTrigger |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 |
| **AI & NLP** | Google Gemini (Generative AI), `sentence-transformers`, RAG vector store |
| **Document Processing** | PyMuPDF (`fitz`), PDFPlumber, ReportLab, python-docx |
| **Deployment** | Vercel (Frontend), Render (Backend), GitHub CI/CD |

---

## 🚀 Getting Started Locally

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+
- Google Gemini API Key

### 1. Clone the Repository
```bash
git clone https://github.com/Numanahmad12/RESUME_TAILOR.git
cd RESUME_TAILOR
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env

# Run FastAPI server
$env:PYTHONPATH="backend/src;."
python -m uvicorn backend.src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit [**http://localhost:3000**](http://localhost:3000) to use the local development instance.

---

## 📦 Deployment Configuration

### Frontend (Vercel)
1. Import repository on [Vercel](https://vercel.com/new).
2. Set Environment Variable:
   - `BACKEND_URL`: `https://resume-tailor-vdyx.onrender.com`
3. Click **Deploy**.

### Backend (Render)
1. Create a **New Web Service** on [Render](https://dashboard.render.com/).
2. Select GitHub repository: `Numanahmad12/RESUME_TAILOR`.
3. Set:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.src.api.app:app --host 0.0.0.0 --port $PORT`
   - **Environment Variable**: `GEMINI_API_KEY`
4. Click **Deploy**.

---

## 📄 License
MIT License. Built with ❤️ for job seekers aiming for top 1% tech roles.
