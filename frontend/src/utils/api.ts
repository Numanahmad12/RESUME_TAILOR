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

/** Always produce a displayable string, even for FastAPI 422 array details. */
export function getErrorMessage(e: unknown): string {
  if (e instanceof ApiError) return e.message;
  if (e instanceof Error) return e.message;
  if (typeof e === 'string') return e;
  try {
    const s = JSON.stringify(e);
    return (s ?? 'Unknown error').slice(0, 500);
  } catch {
    return 'Unknown error';
  }
}

function toDisplayMessage(value: unknown, fallback: string): string {
  if (typeof value === 'string') return value || fallback;
  try {
    return (JSON.stringify(value) ?? fallback).slice(0, 500);
  } catch {
    return fallback;
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
    try {
      const parsed = JSON.parse(body);
      message = toDisplayMessage(
        parsed?.detail ?? parsed?.error ?? body,
        `Request failed with status ${res.status}`
      );
    } catch {}
    throw new ApiError(res.status, toDisplayMessage(message, `Request failed with status ${res.status}`));
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
  achievements?: CertificationEntry[];
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

export interface GapDetail {
  category: string;
  gap: string;
  severity?: 'high' | 'medium' | 'low';
  how_to_fix: string;
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
  gap_details?: GapDetail[];
}

export interface RequirementsCheckResult {
  needs_clarification: boolean;
  missing_required_skills: string[];
  missing_preferred_skills: string[];
  extra_keywords: string[];
  role_title: string;
  prompt_message: string;
}

export interface UserRequirements {
  confirmed_skills: string[];
  additional_context: string;
}

export interface ProjectSuggestion {
  title: string;
  technologies: string[];
  bullets: string[];
  rationale: string;
}

export interface TailoredResult {
  final_id: string;
  resume: ResumeData;
  original_match?: MatchReport;
  match: MatchReport;
  grounding_verified: boolean;
  suggested_projects?: ProjectSuggestion[];
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
  return request<{
    resume_id: string;
    jd_id: string;
    match: MatchReport;
    requirements?: RequirementsCheckResult;
  }>('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId }),
  });
}

export async function checkRequirements(resumeId: string, jdId: string) {
  return request<RequirementsCheckResult>('/requirements/check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId }),
  });
}

export async function tailorResume(
  resumeId: string,
  jdId: string,
  userRequirements?: UserRequirements
) {
  return request<TailoredResult>('/tailor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resume_id: resumeId,
      jd_id: jdId,
      user_requirements: userRequirements,
    }),
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

export async function renderResumeLaTeX(finalId: string): Promise<Blob> {
  const form = new FormData();
  form.append('final_id', finalId);
  return request<Blob>('/render/latex', {
    method: 'POST',
    body: form,
  });
}

// New LLM-based single-step pipeline (legacy)
export async function generateTailoredResume(
  resumeId: string,
  jdId: string,
  format: 'pdf' | 'latex' | 'docx' = 'pdf'
): Promise<Blob> {
  const form = new FormData();
  form.append('resume_id', resumeId);
  form.append('jd_id', jdId);
  form.append('format', format);
  return request<Blob>('/generate-tailored', {
    method: 'POST',
    body: form,
  });
}

// New RAG pipeline (FastAPI expects a JSON body: { resume_id, jd_id, format, user_requirements })
export async function ragPipeline(
  resumeId: string,
  jdId: string,
  format: 'pdf' | 'latex' | 'markdown' = 'pdf',
  userRequirements?: UserRequirements
): Promise<Blob> {
  return request<Blob>('/rag-pipeline', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_id: resumeId, jd_id: jdId, format, user_requirements: userRequirements }),
  });
}

// RAG pipeline types
export interface RagPipelineResult {
  markdown: string;
  resume_id: string;
  jd_id: string;
}

export function getExportUrl(params: {
  finalId?: string | null;
  resumeId?: string | null;
  format?: 'pdf' | 'latex' | 'markdown';
  preview?: boolean;
}): string {
  const qs = new URLSearchParams();
  if (params.finalId) qs.set('final_id', params.finalId);
  if (params.resumeId) qs.set('resume_id', params.resumeId);
  if (params.format) qs.set('format', params.format);
  if (params.preview) qs.set('preview', '1');
  return `/api/export?${qs.toString()}`;
}

export async function exportResume(params: {
  finalId?: string | null;
  resumeId?: string | null;
  format?: 'pdf' | 'latex' | 'markdown';
  preview?: boolean;
  resumeData?: ResumeData | null;
}): Promise<Blob> {
  return request<Blob>('/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      final_id: params.finalId,
      resume_id: params.resumeId,
      format: params.format || 'pdf',
      preview: !!params.preview,
      resume_data: params.resumeData,
    }),
  });
}

