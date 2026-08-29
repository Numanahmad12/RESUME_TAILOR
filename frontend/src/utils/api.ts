/**
 * Typed API client for the Resume Tailoring backend.
 * Uses native fetch — no axios dependency required.
 */

const API_BASE = '/api';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Accept': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    let message = body;
    try { message = JSON.parse(body)?.detail ?? body; } catch {}
    throw new ApiError(res.status, message);
  }

  const contentType = res.headers.get('content-type') ?? '';
  if (contentType.includes('application/json')) {
    return res.json() as Promise<T>;
  }
  return res.blob() as unknown as Promise<T>;
}

// ─── Types ──────────────────────────────────────────────────────────────────

export interface ContactInfo {
  name: string;
  email: string;
  phone: string;
  links: string[];
}

export interface Skill {
  name: string;
  category: string;
}

export interface ExperienceBullet {
  id: string;
  text: string;
  skills_used: string[];
}

export interface ExperienceEntry {
  id: string;
  company: string;
  title: string;
  start_date: string | null;
  end_date: string | null;
  current: boolean;
  bullets: ExperienceBullet[];
}

export interface EducationEntry {
  school: string;
  degree: string;
  dates: string;
  gpa: string | null;
}

export interface ProjectEntry {
  name: string;
  description: string;
  technologies: string[];
  url: string;
}

export interface CertificationEntry {
  name: string;
  issuer: string;
  date: string;
  url: string;
}

export interface ResumeData {
  contact: ContactInfo;
  summary: string;
  skills: Skill[];
  experience: ExperienceEntry[];
  education: EducationEntry[];
  projects: ProjectEntry[];
  certifications: CertificationEntry[];
}

export interface JdData {
  role_title: string;
  seniority_level: string;
  required_skills: string[];
  preferred_skills: string[];
  min_years_experience: number;
  responsibilities: string[];
  keywords_for_ats: string[];
}

export interface MatchReport {
  overall_score: number;
  keyword_coverage: number;
  experience_match: number;
  responsibility_similarity: number;
  ats_formatting_score?: number;
  impact_metrics_score?: number;
  fit_verdict?: string;
  fit_summary?: string;
  matched_skills?: string[];
  missing_required_skills?: string[];
  missing_preferred_skills?: string[];
  gaps: string[];
  suggestions: string[];
  high_impact_improvements?: string[];
}

export interface PatchAction {
  target: string;
  action: string;
  original: string;
  proposed: string;
  reason: string;
}

// ─── API Calls ───────────────────────────────────────────────────────────────

export async function uploadResume(file: File) {
  const form = new FormData();
  form.append('file', file);
  return request<{ resume_id: string; resume: ResumeData }>('/upload/resume', {
    method: 'POST',
    body: form,
  });
}

export async function uploadJd(payload: { file?: File; text?: string }) {
  const form = new FormData();
  if (payload.file) form.append('file', payload.file);
  if (payload.text) form.append('text', payload.text);
  return request<{ jd_id: string; jd: JdData }>('/upload/jd', {
    method: 'POST',
    body: form,
  });
}

export async function analyzeMatch(resumeId: string, jdId: string) {
  return request<{ resume_id: string; jd_id: string; match: MatchReport }>('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId }),
  });
}

export async function generatePatches(
  resumeId: string,
  jdId: string,
  matchReport: MatchReport
) {
  return request<{ generation_id: string; patches: PatchAction[] }>('/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId, match_report: matchReport }),
  });
}

export async function applyPatches(resumeId: string, generationId: string) {
  return request<{ final_id: string; resume: ResumeData }>('/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, generation_id: generationId }),
  });
}

export async function renderResume(finalId: string, format: 'pdf' | 'docx'): Promise<Blob> {
  const form = new FormData();
  form.append('final_id', finalId);
  return request<Blob>(`/render/${format}`, {
    method: 'POST',
    body: form,
  });
}
