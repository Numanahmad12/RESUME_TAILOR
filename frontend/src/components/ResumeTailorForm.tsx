import React, { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import {
  Upload, FileText, BarChart3, CheckSquare, Download, ChevronRight,
  AlertCircle, Sparkles, ArrowRight, CheckCircle2, RefreshCw,
  ExternalLink, Check, X, TrendingUp, ShieldCheck, Zap
} from 'lucide-react';
import { usePipeline } from '../hooks/useResumePipeline';
import * as api from '../utils/api';

// ─── Sub-components ─────────────────────────────────────────────────────────

function ScoreBar({ value, label, color, subtitle }: { value: number; label: string; color: string; subtitle?: string }) {
  const pct = Math.min(Math.max(Math.round((value || 0) * 100), 0), 100);
  return (
    <div>
      <div className="flex justify-between items-baseline text-xs mb-1.5">
        <span className="text-slate-300 font-medium">{label}</span>
        <span className="font-bold text-sm" style={{ color }}>{pct}%</span>
      </div>
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden border border-slate-700/60">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      {subtitle && <p className="text-[11px] text-slate-400 mt-1">{subtitle}</p>}
    </div>
  );
}

function PatchCard({ patch, index }: { patch: api.PatchAction; index: number }) {
  const [expanded, setExpanded] = useState(true);

  // ── Project suggestion card ──────────────────────────────────────
  if (patch.action === 'suggest_project') {
    return (
      <div className="rounded-xl p-4 border border-amber-600/40 bg-amber-950/20 animate-fade-in" style={{ animationDelay: `${index * 60}ms` }}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-amber-900/60 border border-amber-600/50 text-amber-300">💡 Suggested Project</span>
          <span className="text-xs text-amber-400 font-medium">{patch.reason}</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed bg-slate-900/60 rounded-lg p-3 border border-amber-800/30">
          {patch.proposed}
        </p>
        <p className="text-xs text-slate-500 mt-2 italic">Add this project to your resume to demonstrate the missing skills highlighted above.</p>
      </div>
    );
  }

  // ── Missing skills card ──────────────────────────────────────────
  if (patch.action === 'add_skills') {
    let skills: string[] = [];
    try { skills = JSON.parse(patch.proposed); } catch {}
    return (
      <div className="rounded-xl p-4 border border-red-600/40 bg-red-950/20 animate-fade-in" style={{ animationDelay: `${index * 60}ms` }}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-red-900/60 border border-red-600/50 text-red-300">⚠️ Missing Required Skills</span>
        </div>
        <div className="flex flex-wrap gap-1.5 mb-2">
          {skills.map((s, i) => (
            <span key={i} className="text-xs px-2.5 py-1 rounded-md bg-red-950 border border-red-700/50 text-red-300 font-medium">{s}</span>
          ))}
        </div>
        <p className="text-xs text-slate-400 italic">{patch.reason}</p>
      </div>
    );
  }

  // ── Standard rewrite / reorder card ─────────────────────────────
  const badgeClass = patch.action === 'reorder'
    ? 'badge-reorder'
    : patch.action === 'rewrite'
    ? 'badge-rewrite'
    : 'badge-add';

  return (
    <div className="patch-card rounded-xl p-4 transition-all duration-200 border border-slate-700/60 bg-slate-900/60 hover:border-indigo-500/40 animate-fade-in" style={{ animationDelay: `${index * 60}ms` }}>
      <div className="flex items-start justify-between gap-3 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className={`badge ${badgeClass}`}>{patch.action}</span>
          <code className="text-xs text-indigo-300 bg-indigo-950/70 border border-indigo-800/50 px-2.5 py-1 rounded font-mono font-medium">
            {patch.target}
          </code>
        </div>
        <ChevronRight size={16} className={`text-slate-400 mt-1 transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} />
      </div>

      {expanded && (
        <div className="mt-3.5 space-y-3 animate-fade-in">
          <div className="grid md:grid-cols-2 gap-3">
            <div className="rounded-lg p-3.5 bg-red-950/20 border border-red-800/30">
              <p className="text-xs font-semibold text-red-400 mb-1.5 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
                Original
              </p>
              <p className="text-sm text-slate-300 leading-relaxed font-normal">{patch.original || '—'}</p>
            </div>
            <div className="rounded-lg p-3.5 bg-emerald-950/25 border border-emerald-700/40">
              <p className="text-xs font-semibold text-emerald-400 mb-1.5 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                Tailored
              </p>
              <p className="text-sm text-emerald-100 leading-relaxed font-medium">{patch.proposed || '—'}</p>
            </div>
          </div>
          {patch.reason && (
            <p className="text-xs text-indigo-300/80 italic flex items-center gap-1.5">
              <span>💡</span> {patch.reason}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Step 1: Upload ─────────────────────────────────────────────────────────

function StepUpload() {
  const {
    resumeFile, jdFile, jdText,
    setResumeFile, setJdFile, setJdText,
    setResumeUploaded, setJdUploaded,
    setLoading, setError, goToStep, isLoading, loadingMessage,
    resumeId, jdId, resumeData, jdData
  } = usePipeline();

  const [jdMode, setJdMode] = useState<'text' | 'file'>('text');
  const [localJdText, setLocalJdText] = useState(jdText || '');
  const [resumeDragging, setResumeDragging] = useState(false);
  const [jdDragging, setJdDragging] = useState(false);

  const handleResumeDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setResumeDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleResumeFile(file);
  }, []);

  const handleResumeFile = async (file: File) => {
    setResumeFile(file);
    setLoading(true, 'Parsing resume structure & preserving template…');
    try {
      const res = await api.uploadResume(file);
      setResumeUploaded(res.resume_id, res.resume);
      toast.success(`Resume parsed: ${res.resume.contact.name || file.name}`);
    } catch (e: any) {
      setError(e.message);
      toast.error('Resume upload error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJdDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setJdDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleJdFile(file);
  }, []);

  const handleJdFile = async (file: File) => {
    setJdFile(file);
    setLoading(true, 'Extracting job requirements & keywords…');
    try {
      const res = await api.uploadJd({ file });
      setJdUploaded(res.jd_id, res.jd);
      toast.success(`JD analyzed: ${res.jd.role_title}`);
    } catch (e: any) {
      setError(e.message);
      toast.error('JD upload error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProcessJdText = async () => {
    if (!localJdText.trim()) return null;
    setJdText(localJdText.trim());
    setLoading(true, 'Analyzing job description text…');
    try {
      const res = await api.uploadJd({ text: localJdText.trim() });
      setJdUploaded(res.jd_id, res.jd);
      toast.success(`JD analyzed: ${res.jd.role_title}`);
      return res.jd_id;
    } catch (e: any) {
      setError(e.message);
      toast.error('JD analysis error: ' + e.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const handleProceed = async () => {
    let currentJdId: string | null | undefined = jdId;
    if (!currentJdId && localJdText.trim()) {
      const newJdId = await handleProcessJdText();
      currentJdId = newJdId ?? null;
    }
    if (!resumeId) {
      toast.error('Please upload your resume first.');
      return;
    }
    if (!currentJdId) {
      toast.error('Please provide a job description (file or text).');
      return;
    }
    goToStep('analyze');
  };

  const canProceed = resumeId && (jdId || localJdText.trim().length > 20) && !isLoading;

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="grid md:grid-cols-2 gap-6">
        {/* Resume Box */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-200">
            1. Your Resume (PDF or DOCX) <span className="text-indigo-400">*</span>
          </label>
          <div
            className={`upload-zone rounded-2xl p-6 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
              resumeDragging ? 'border-indigo-500 bg-indigo-950/30' : resumeFile ? 'border-emerald-500/60 bg-emerald-950/20' : 'border-slate-700 bg-slate-900/40 hover:border-indigo-500/50'
            }`}
            onDragOver={(e) => { e.preventDefault(); setResumeDragging(true); }}
            onDragLeave={() => setResumeDragging(false)}
            onDrop={handleResumeDrop}
            onClick={() => document.getElementById('input-resume-file')?.click()}
          >
            <input
              id="input-resume-file"
              type="file"
              accept=".pdf,.docx,.doc"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleResumeFile(f); }}
            />
            {resumeFile ? (
              <div className="py-2">
                <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-500/20 flex items-center justify-center mb-3">
                  <CheckCircle2 size={24} className="text-emerald-400" />
                </div>
                <p className="font-semibold text-emerald-300 text-sm truncate">{resumeFile.name}</p>
                <p className="text-xs text-slate-400 mt-1">{(resumeFile.size / 1024).toFixed(1)} KB · Template Preserved</p>
                {resumeData && resumeData.contact.name && (
                  <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-700/50 text-emerald-300 text-xs">
                    {resumeData.contact.name} ({resumeData.skills.length} skills · {resumeData.experience.length} roles)
                  </span>
                )}
              </div>
            ) : (
              <div className="py-4">
                <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-600/15 flex items-center justify-center mb-3 text-indigo-400">
                  <Upload size={24} />
                </div>
                <p className="font-semibold text-slate-200 text-sm">Drop Resume or click to browse</p>
                <p className="text-xs text-slate-400 mt-1">PDF or DOCX (up to 10 MB)</p>
              </div>
            )}
          </div>
        </div>

        {/* JD Box */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-semibold text-slate-200">
              2. Target Job Description <span className="text-indigo-400">*</span>
            </label>
            <div className="flex gap-1 bg-slate-800/80 p-0.5 rounded-lg border border-slate-700 text-xs">
              <button
                type="button"
                className={`px-2.5 py-1 rounded-md transition-all ${jdMode === 'text' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'}`}
                onClick={() => setJdMode('text')}
              >
                Paste Text
              </button>
              <button
                type="button"
                className={`px-2.5 py-1 rounded-md transition-all ${jdMode === 'file' ? 'bg-indigo-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'}`}
                onClick={() => setJdMode('file')}
              >
                Upload File
              </button>
            </div>
          </div>

          {jdMode === 'text' ? (
            <div className="space-y-2">
              <textarea
                className="w-full h-44 rounded-2xl p-3.5 text-xs font-mono bg-slate-900/60 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none resize-none transition-all"
                placeholder="Paste job posting text (e.g. Job Title, Requirements, Qualifications, Responsibilities)..."
                value={localJdText}
                onChange={(e) => setLocalJdText(e.target.value)}
                onBlur={() => { if (localJdText.trim().length > 20 && !jdId) handleProcessJdText(); }}
              />
              {jdData && (
                <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-800/40 px-3 py-1.5 rounded-lg">
                  <CheckCircle2 size={13} />
                  <span>Target: <strong>{jdData.role_title}</strong> ({jdData.required_skills.length} required skills)</span>
                </div>
              )}
            </div>
          ) : (
            <div
              className={`upload-zone rounded-2xl p-6 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
                jdDragging ? 'border-indigo-500 bg-indigo-950/30' : jdFile ? 'border-emerald-500/60 bg-emerald-950/20' : 'border-slate-700 bg-slate-900/40 hover:border-indigo-500/50'
              }`}
              onDragOver={(e) => { e.preventDefault(); setJdDragging(true); }}
              onDragLeave={() => setJdDragging(false)}
              onDrop={handleJdDrop}
              onClick={() => document.getElementById('input-jd-file')?.click()}
            >
              <input
                id="input-jd-file"
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) handleJdFile(f); }}
              />
              {jdFile ? (
                <div className="py-2">
                  <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-500/20 flex items-center justify-center mb-3">
                    <CheckCircle2 size={24} className="text-emerald-400" />
                  </div>
                  <p className="font-semibold text-emerald-300 text-sm truncate">{jdFile.name}</p>
                  <p className="text-xs text-slate-400 mt-1">{(jdFile.size / 1024).toFixed(1)} KB · Ready</p>
                  {jdData && (
                    <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-700/50 text-emerald-300 text-xs">
                      Role: {jdData.role_title} ({jdData.required_skills.length} skills)
                    </span>
                  )}
                </div>
              ) : (
                <div className="py-4">
                  <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-600/15 flex items-center justify-center mb-3 text-indigo-400">
                    <FileText size={24} />
                  </div>
                  <p className="font-semibold text-slate-200 text-sm">Drop Job Description file</p>
                  <p className="text-xs text-slate-400 mt-1">PDF, DOCX, or TXT</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center gap-3 py-2.5 text-indigo-300 bg-indigo-950/40 border border-indigo-800/40 rounded-xl animate-pulse">
          <div className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">{loadingMessage}</span>
        </div>
      )}

      <div className="flex justify-end pt-2">
        <button
          type="button"
          className="btn-primary flex items-center gap-2 text-sm font-semibold px-7 py-3 rounded-xl transition-all shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50"
          disabled={!canProceed}
          onClick={handleProceed}
        >
          <span>Calculate Honest ATS Score & Gaps</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ─── Step 2: Analyze ────────────────────────────────────────────────────────

function StepAnalyze() {
  const {
    resumeId, jdId, matchReport, jdData,
    setMatchReport, setPatches, setLoading, setError, goToStep,
    isLoading, loadingMessage,
  } = usePipeline();

  const runAnalysis = useCallback(async () => {
    if (!resumeId || !jdId) return;
    setLoading(true, 'Running comprehensive ATS parser & gap scoring…');
    try {
      const res = await api.analyzeMatch(resumeId, jdId);
      setMatchReport(res.match);
      toast.success('Honest ATS evaluation calculated!');
    } catch (e: any) {
      setError(e.message);
      toast.error('Analysis error: ' + e.message);
    } finally {
      setLoading(false);
    }
  }, [resumeId, jdId, setMatchReport, setLoading, setError]);

  useEffect(() => {
    if (!matchReport && resumeId && jdId && !isLoading) {
      runAnalysis();
    }
  }, [matchReport, resumeId, jdId, isLoading, runAnalysis]);

  const generatePatches = async () => {
    if (!resumeId || !jdId || !matchReport) return;
    setLoading(true, 'Generating grounded ATS patches while preserving original template…');
    try {
      const res = await api.generatePatches(resumeId, jdId, matchReport);
      setPatches(res.generation_id, res.patches);
      toast.success(`${res.patches.length} tailored patches generated!`);
      goToStep('review');
    } catch (e: any) {
      setError(e.message);
      toast.error('Patch generation error: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (score: number) => {
    if (score >= 80) return '#10b981';
    if (score >= 55) return '#f59e0b';
    return '#ef4444';
  };

  const overallScore = matchReport ? Math.round(matchReport.overall_score) : 0;

  return (
    <div className="space-y-6 animate-slide-up">
      {isLoading && !matchReport ? (
        <div className="card p-12 text-center space-y-4">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 animate-spin">
            <RefreshCw size={26} />
          </div>
          <h3 className="text-lg font-bold text-slate-100">Evaluating ATS Match & Job Fit...</h3>
          <p className="text-sm text-slate-400">{loadingMessage || 'Evaluating hard skills, experience duration, bullet metrics, and formatting health'}</p>
        </div>
      ) : matchReport ? (
        <>
          {/* Main Score & Fit Verdict Card */}
          <div className="card p-6 md:p-7 border border-slate-700/60 bg-slate-900/70 rounded-2xl space-y-6">
            <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-slate-800">
              <div className="relative w-32 h-32 flex-shrink-0 flex items-center justify-center">
                <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="3.2" />
                  <circle
                    cx="18" cy="18" r="15.9" fill="none"
                    stroke={scoreColor(overallScore)}
                    strokeWidth="3.2"
                    strokeDasharray={`${overallScore} ${100 - overallScore}`}
                    strokeLinecap="round"
                    className="transition-all duration-1000"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-3xl font-extrabold text-slate-100">{overallScore}</span>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">ATS Score</span>
                </div>
              </div>

              <div className="space-y-1.5 text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start gap-2.5 flex-wrap">
                  <h3 className="text-2xl font-extrabold text-slate-100">Job Fit Evaluation</h3>
                  <span
                    className="text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wide border"
                    style={{
                      background: overallScore >= 80 ? 'rgba(16,185,129,0.15)' : overallScore >= 55 ? 'rgba(245,158,11,0.15)' : 'rgba(239,68,68,0.15)',
                      borderColor: scoreColor(overallScore),
                      color: scoreColor(overallScore)
                    }}
                  >
                    {matchReport.fit_verdict || (overallScore >= 80 ? 'Strong Fit' : overallScore >= 55 ? 'Moderate Fit' : 'Low Fit')}
                  </span>
                </div>
                <p className="text-xs md:text-sm text-slate-300 leading-relaxed font-normal">
                  {matchReport.fit_summary || 'Evaluating your resume compatibility against the hiring manager requirements.'}
                </p>
                {jdData && (
                  <p className="text-xs text-indigo-300 font-mono pt-1">
                    Target Role: <strong>{jdData.role_title}</strong> ({jdData.seniority_level} · {jdData.min_years_experience}y required)
                  </p>
                )}
              </div>
            </div>

            {/* 5-Factor ATS Dimension Breakdown */}
            <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-700/40">
                <ScoreBar value={matchReport.keyword_coverage} label="Hard Skills Match" color="#ff2e2e" subtitle="Matches required technical terms" />
              </div>
              <div className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-700/40">
                <ScoreBar value={matchReport.experience_match} label="Experience Fit" color="#10b981" subtitle="Candidate years vs JD minimum" />
              </div>
              <div className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-700/40">
                <ScoreBar value={matchReport.responsibility_similarity} label="Responsibility Match" color="#f59e0b" subtitle="Core duty keyword overlap" />
              </div>
              <div className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-700/40">
                <ScoreBar value={matchReport.impact_metrics_score || 0.5} label="Impact & Quantification" color="#38bdf8" subtitle="KPIs, %, $, and numbers in bullets" />
              </div>
              <div className="bg-slate-800/40 p-3.5 rounded-xl border border-slate-700/40">
                <ScoreBar value={matchReport.ats_formatting_score || 0.9} label="ATS Readability" color="#a855f7" subtitle="Contact & section structure health" />
              </div>
            </div>

            {/* Matched vs Missing Skills Tags */}
            <div className="space-y-3 pt-2">
              {matchReport.matched_skills && matchReport.matched_skills.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-1.5">
                    <Check size={14} /> Matched Keywords & Technologies ({matchReport.matched_skills.length}):
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {matchReport.matched_skills.map((s, i) => (
                      <span key={i} className="text-xs px-2.5 py-0.5 rounded-md bg-emerald-950/60 border border-emerald-700/40 text-emerald-300 font-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {matchReport.missing_required_skills && matchReport.missing_required_skills.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-red-400 mb-2 flex items-center gap-1.5">
                    <X size={14} /> Missing Required Skills ({matchReport.missing_required_skills.length}):
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {matchReport.missing_required_skills.map((s, i) => (
                      <span key={i} className="text-xs px-2.5 py-0.5 rounded-md bg-red-950/60 border border-red-700/40 text-red-300 font-medium">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Actionable High-Impact Roadmap */}
          {matchReport.high_impact_improvements && matchReport.high_impact_improvements.length > 0 && (
            <div className="card p-5 border border-indigo-800/40 bg-indigo-950/25 rounded-2xl">
              <h4 className="text-sm font-bold text-indigo-300 mb-3 flex items-center gap-2">
                <TrendingUp size={17} className="text-indigo-400" />
                Actionable Improvements to Boost ATS Score
              </h4>
              <ul className="space-y-2.5">
                {matchReport.high_impact_improvements.map((item, i) => (
                  <li key={i} className="text-xs text-slate-200 flex items-start gap-2.5 bg-slate-900/60 p-2.5 rounded-xl border border-indigo-900/40">
                    <span className="w-5 h-5 rounded-full bg-indigo-600/30 text-indigo-300 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Gaps and AI suggestions */}
          <div className="grid md:grid-cols-2 gap-5">
            {matchReport.gaps && matchReport.gaps.length > 0 && (
              <div className="card p-5 border border-red-900/30 bg-red-950/15 rounded-2xl">
                <h4 className="text-sm font-semibold text-red-400 mb-3 flex items-center gap-2">
                  <AlertCircle size={16} /> Detailed Gap Audit
                </h4>
                <ul className="space-y-2">
                  {matchReport.gaps.map((g, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-2 leading-relaxed">
                      <span className="text-red-400 mt-0.5">•</span>
                      <span>{g}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {matchReport.suggestions && matchReport.suggestions.length > 0 && (
              <div className="card p-5 border border-slate-700/60 bg-slate-900/50 rounded-2xl">
                <h4 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
                  <Sparkles size={16} className="text-indigo-400" /> Strategic Suggestions
                </h4>
                <ul className="space-y-2">
                  {matchReport.suggestions.map((s, i) => (
                    <li key={i} className="text-xs text-slate-300 flex items-start gap-2 leading-relaxed">
                      <span className="text-indigo-400 mt-0.5">→</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex justify-between items-center pt-2">
            <button
              type="button"
              className="btn-secondary text-sm"
              onClick={() => goToStep('upload')}
            >
              ← Back to Upload
            </button>
            <button
              type="button"
              className="btn-primary text-sm flex items-center gap-2"
              onClick={generatePatches}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>{loadingMessage}</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Generate Grounded Tailored Patches</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </>
      ) : (
        <div className="card p-8 text-center space-y-4">
          <p className="text-slate-300">Ready to score candidate match against JD requirements.</p>
          <button type="button" className="btn-primary mx-auto" onClick={runAnalysis}>
            Run Match Analysis
          </button>
        </div>
      )}
    </div>
  );
}

// ─── Step 3: Review Patches ────────────────────────────────────────────────

function StepReview() {
  const {
    patches, resumeId, generationId, setFinalResume,
    setLoading, setError, goToStep, isLoading, loadingMessage
  } = usePipeline();

  const applyAll = async () => {
    if (!resumeId || !generationId) return;
    setLoading(true, 'Applying accepted patches while preserving original template structure…');
    try {
      const res = await api.applyPatches(resumeId, generationId);
      setFinalResume(res.final_id, res.resume);
      toast.success('Tailored resume created with template preserved!');
      goToStep('download');
    } catch (e: any) {
      setError(e.message);
      toast.error('Error applying patches: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div>
          <h3 className="text-lg font-bold text-slate-100">Review Tailored Patches</h3>
          <p className="text-xs text-slate-400">Preserves your original resume layout, dates, and companies while optimizing keywords and bullet impact.</p>
        </div>
        <span className="px-3 py-1 rounded-full bg-indigo-950 border border-indigo-700/50 text-indigo-300 text-xs font-semibold">
          {patches.length} Changes
        </span>
      </div>

      {patches.length === 0 ? (
        <div className="card p-8 text-center bg-slate-900/60 rounded-2xl">
          <CheckSquare size={32} className="mx-auto mb-3 text-emerald-400" />
          <p className="text-slate-300 font-medium">Your resume is already optimal for this position!</p>
          <p className="text-xs text-slate-500 mt-1">No modifications needed to pass ATS thresholds.</p>
        </div>
      ) : (
        <div className="space-y-3.5">
          {patches.map((p, i) => <PatchCard key={i} patch={p} index={i} />)}
        </div>
      )}

      <div className="flex justify-between items-center pt-3">
        <button type="button" className="btn-secondary text-sm" onClick={() => goToStep('analyze')}>
          ← Back to Analysis
        </button>
        <button
          type="button"
          className="btn-success text-sm font-semibold flex items-center gap-2 px-6 py-3 rounded-xl shadow-lg shadow-emerald-600/20 hover:shadow-emerald-600/40"
          onClick={applyAll}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>{loadingMessage}</span>
            </>
          ) : (
            <>
              <CheckSquare size={16} />
              <span>Apply Patches & Render Resume</span>
              <ArrowRight size={16} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ─── Step 4: Download ──────────────────────────────────────────────────────

function StepDownload() {
  const { finalId, finalResumeData, reset } = usePipeline();
  const [downloading, setDownloading] = useState<string | null>(null);

  const download = async (format: 'pdf' | 'docx') => {
    if (!finalId) return;
    setDownloading(format);
    try {
      const blob = await api.renderResume(finalId, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `tailored_resume.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      // Wait 15 seconds before revoking blob URL so browser finishes file write
      setTimeout(() => URL.revokeObjectURL(url), 15000);
      toast.success(`Downloaded tailored_resume.${format}!`);
    } catch (e: any) {
      toast.error(`Download failed: ${e.message}`);
    } finally {
      setDownloading(null);
    }
  };

  const previewInNewTab = async () => {
    if (!finalId) return;
    setDownloading('preview');
    try {
      const blob = await api.renderResume(finalId, 'pdf');
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
      toast.success('Opened PDF preview in new tab!');
    } catch (e: any) {
      toast.error(`Preview error: ${e.message}`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="card p-8 md:p-10 text-center bg-slate-900/70 border border-slate-700/60 rounded-2xl">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mb-4">
          <ShieldCheck size={32} className="text-emerald-400" />
        </div>
        <h3 className="text-2xl font-extrabold text-slate-100 mb-2">Tailored Resume Ready!</h3>
        <p className="text-slate-300 text-sm max-w-lg mx-auto mb-6 leading-relaxed">
          Original resume template and section structure preserved. Keyword alignment and bullet enhancements applied for ATS passing.
        </p>

        {finalResumeData && (
          <div className="text-left bg-slate-950/70 border border-slate-800 p-5 rounded-xl max-w-lg mx-auto mb-8 space-y-2">
            <div className="flex justify-between items-center">
              <span className="font-bold text-slate-100">{finalResumeData.contact.name || 'Tailored Resume'}</span>
              <span className="text-xs bg-emerald-950 border border-emerald-800/50 text-emerald-300 px-2.5 py-0.5 rounded-full font-medium">ATS Verified</span>
            </div>
            {finalResumeData.contact.email && (
              <p className="text-xs text-slate-400">{finalResumeData.contact.email} {finalResumeData.contact.phone ? `· ${finalResumeData.contact.phone}` : ''}</p>
            )}
            <p className="text-xs text-indigo-300 font-mono pt-1">
              ✓ {finalResumeData.skills.length} Technical Skills · {finalResumeData.experience.length} Roles · {finalResumeData.education.length} Education
            </p>
          </div>
        )}

        <div className="flex flex-wrap gap-4 justify-center items-center">
          <button
            type="button"
            className="btn-success font-semibold px-6 py-3.5 text-sm flex items-center gap-2 rounded-xl"
            onClick={() => download('pdf')}
            disabled={!!downloading}
          >
            {downloading === 'pdf' ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Download size={16} />
            )}
            <span>Download PDF</span>
          </button>

          <button
            type="button"
            className="btn-primary font-semibold px-6 py-3.5 text-sm flex items-center gap-2 rounded-xl"
            onClick={previewInNewTab}
            disabled={!!downloading}
          >
            {downloading === 'preview' ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <ExternalLink size={16} />
            )}
            <span>Preview in Browser</span>
          </button>

          <button
            type="button"
            className="btn-secondary font-semibold px-6 py-3.5 text-sm flex items-center gap-2 rounded-xl"
            onClick={() => download('docx')}
            disabled={!!downloading}
          >
            {downloading === 'docx' ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Download size={16} />
            )}
            <span>Download DOCX</span>
          </button>
        </div>
      </div>

      <div className="text-center pt-2">
        <button
          type="button"
          className="text-xs text-slate-400 hover:text-slate-200 transition-colors inline-flex items-center gap-1.5"
          onClick={() => reset()}
        >
          <RefreshCw size={13} />
          <span>Start Over with a New Resume / Job Posting</span>
        </button>
      </div>
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

const STEPS: { key: string; label: string; icon: React.ReactNode }[] = [
  { key: 'upload', label: 'Upload', icon: <Upload size={15} /> },
  { key: 'analyze', label: 'ATS & Fit Score', icon: <BarChart3 size={15} /> },
  { key: 'review', label: 'Review Patches', icon: <CheckSquare size={15} /> },
  { key: 'download', label: 'Export Resume', icon: <Download size={15} /> },
];

export default function ResumeTailorForm() {
  const { currentStep, error } = usePipeline();
  const stepIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div className="max-w-3xl mx-auto">
      {/* Wizard Progress bar */}
      <div className="flex items-center gap-2 mb-8 bg-slate-900/60 p-2.5 rounded-2xl border border-slate-800/80">
        {STEPS.map((step, i) => (
          <React.Fragment key={step.key}>
            <div
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-300 ${
                step.key === currentStep
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : i < stepIndex
                  ? 'text-emerald-400 bg-emerald-950/40 border border-emerald-800/30'
                  : 'text-slate-500'
              }`}
            >
              {i < stepIndex ? (
                <CheckCircle2 size={15} className="text-emerald-400" />
              ) : (
                step.icon
              )}
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 transition-colors duration-500 ${i < stepIndex ? 'bg-emerald-500/70' : 'bg-slate-800'}`} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Global Error Notice */}
      {error && (
        <div className="mb-5 rounded-xl px-4 py-3 flex items-center gap-3 text-sm bg-red-950/40 border border-red-800/50 animate-fade-in">
          <AlertCircle size={18} className="text-red-400 flex-shrink-0" />
          <span className="text-red-200">{error}</span>
        </div>
      )}

      {/* Main Step Container */}
      <div className="card p-6 md:p-8 bg-slate-900/70 border border-slate-700/60 rounded-2xl backdrop-blur-md shadow-2xl">
        {currentStep === 'upload' && <StepUpload />}
        {currentStep === 'analyze' && <StepAnalyze />}
        {currentStep === 'review' && <StepReview />}
        {currentStep === 'download' && <StepDownload />}
      </div>
    </div>
  );
}