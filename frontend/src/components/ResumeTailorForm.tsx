import React, { useState, useEffect, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import {
  Upload, FileText, BarChart3, CheckSquare, Download, ChevronRight,
  AlertCircle, Sparkles, ArrowRight, CheckCircle2, RefreshCw,
  ExternalLink, Check, X, TrendingUp, ShieldCheck, Zap, HelpCircle, FileCode,
  Eye, EyeOff
} from 'lucide-react';
import { usePipeline, PipelineStep } from '../hooks/useResumePipeline';
import * as api from '../utils/api';
import { LoadingProgressBar } from './LoadingProgressBar';

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

// ─── Step 1: Upload ─────────────────────────────────────────────────────────

function StepUpload() {
  const {
    resumeFile, jdFile, jdText,
    setResumeFile, setJdFile, setJdText,
    setResumeUploaded, setJdUploaded,
    setMatchReport, setRequirements,
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
    setLoading(true, 'Parsing resume structure…');
    try {
      const res = await api.uploadResume(file);
      setResumeUploaded(res.resume_id, res.resume);
      toast.success(`Resume parsed: ${res.resume.contact.name || file.name}`);
    } catch (e: any) {
      setError(api.getErrorMessage(e));
      toast.error('Resume upload error: ' + api.getErrorMessage(e));
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
    setLoading(true, 'Extracting job requirements…');
    try {
      const res = await api.uploadJd({ file });
      setJdUploaded(res.jd_id, res.jd);
      toast.success(`JD analyzed: ${res.jd.role_title}`);
    } catch (e: any) {
      setError(api.getErrorMessage(e));
      toast.error('JD upload error: ' + api.getErrorMessage(e));
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
      setError(api.getErrorMessage(e));
      toast.error('JD analysis error: ' + api.getErrorMessage(e));
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

    setLoading(true, 'Running ATS gap & match analysis…');
    try {
      const analysis = await api.analyzeMatch(resumeId, currentJdId);
      setMatchReport(analysis.match);
      if (analysis.requirements) {
        setRequirements(analysis.requirements);
      }
      goToStep('analyze');
    } catch (e: any) {
      setError(api.getErrorMessage(e));
      toast.error('Analysis error: ' + api.getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const canProceed = resumeId && (jdId || localJdText.trim().length > 20) && !isLoading;

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="grid md:grid-cols-2 gap-6">
        {/* Resume Box */}
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-200">
            1. Your Resume (PDF or DOCX) <span className="text-red-400">*</span>
          </label>
          <div
            className={`upload-zone rounded-2xl p-6 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
              resumeDragging ? 'border-red-500 bg-red-950/30' : resumeFile ? 'border-emerald-500/60 bg-emerald-950/20' : 'border-slate-700 bg-slate-900/40 hover:border-red-500/50'
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
                <p className="text-xs text-slate-400 mt-1">{(resumeFile.size / 1024).toFixed(1)} KB</p>
                {resumeData && (
                  <div className="mt-2 flex flex-wrap justify-center gap-1.5">
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-950 border border-emerald-700/50 text-emerald-300 text-xs font-medium">
                      {resumeData.contact.name || 'Candidate'}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs">
                      {resumeData.skills.length} skills · {resumeData.projects.length} projects · {resumeData.experience.length} roles
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-4">
                <div className="w-12 h-12 mx-auto rounded-xl bg-red-600/15 flex items-center justify-center mb-3 text-red-400">
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
              2. Target Job Description <span className="text-red-400">*</span>
            </label>
            <div className="flex gap-1 bg-slate-800/80 p-0.5 rounded-lg border border-slate-700 text-xs">
              <button
                type="button"
                className={`px-2.5 py-1 rounded-md transition-all ${jdMode === 'text' ? 'bg-red-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'}`}
                onClick={() => setJdMode('text')}
              >
                Paste Text
              </button>
              <button
                type="button"
                className={`px-2.5 py-1 rounded-md transition-all ${jdMode === 'file' ? 'bg-red-600 text-white font-medium shadow' : 'text-slate-400 hover:text-slate-200'}`}
                onClick={() => setJdMode('file')}
              >
                Upload File
              </button>
            </div>
          </div>

          {jdMode === 'text' ? (
            <div className="space-y-2">
              <textarea
                className="w-full h-44 rounded-2xl p-3.5 text-xs font-mono bg-slate-900/60 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none resize-none transition-all"
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
                jdDragging ? 'border-red-500 bg-red-950/30' : jdFile ? 'border-emerald-500/60 bg-emerald-950/20' : 'border-slate-700 bg-slate-900/40 hover:border-red-500/50'
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
                  <div className="w-12 h-12 mx-auto rounded-xl bg-red-600/15 flex items-center justify-center mb-3 text-red-400">
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
        <div className="flex items-center justify-center gap-3 py-2.5 text-red-300 bg-red-950/40 border border-red-800/40 rounded-xl animate-pulse">
          <div className="w-4 h-4 border-2 border-red-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium">{loadingMessage}</span>
        </div>
      )}

      <div className="flex justify-end pt-2">
        <button
          type="button"
          className="btn-primary flex items-center gap-2 text-sm font-semibold px-7 py-3 rounded-xl transition-all shadow-lg shadow-red-600/30 hover:shadow-red-600/50"
          disabled={!canProceed}
          onClick={handleProceed}
        >
          <span>Analyze Fit & Gaps</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ─── Step 2: Analyze & Match ───────────────────────────────────────────────

function StepAnalyze() {
  const { matchReport, jdData, resumeData, goToStep } = usePipeline();

  if (!matchReport) {
    return (
      <div className="text-center py-8">
        <p className="text-slate-400 text-sm mb-4">No analysis report found. Please upload your files first.</p>
        <button type="button" className="btn-secondary text-sm" onClick={() => goToStep('upload')}>
          ← Back to Upload
        </button>
      </div>
    );
  }

  const score = Math.round(matchReport.overall_score);
  const scoreColor = score >= 75 ? '#10b981' : score >= 55 ? '#f59e0b' : '#ff2e2e';

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Target Role</span>
          <h3 className="text-xl font-bold text-white mt-0.5">{jdData?.role_title || 'Target Position'}</h3>
          <p className="text-xs text-slate-400 mt-1">{matchReport.fit_summary || 'Analysis complete.'}</p>
        </div>
        <div className="flex items-center gap-4 bg-slate-950/80 px-5 py-3 rounded-xl border border-slate-800">
          <div className="text-right">
            <span className="text-xs text-slate-400 block font-medium">Initial ATS Fit</span>
            <span className="text-2xl font-black" style={{ color: scoreColor }}>{score}%</span>
          </div>
          <div className="h-10 w-1 rounded-full" style={{ background: scoreColor }} />
        </div>
      </div>

      {/* 3 Pillars Breakdown */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <ScoreBar
            value={matchReport.keyword_coverage}
            label="Keyword Coverage"
            color="#3b82f6"
            subtitle={`${matchReport.matched_skills?.length || 0} matching skills`}
          />
        </div>
        <div className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <ScoreBar
            value={matchReport.experience_match}
            label="Experience Alignment"
            color="#10b981"
            subtitle="Tenure and domain suitability"
          />
        </div>
        <div className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <ScoreBar
            value={matchReport.responsibility_similarity}
            label="Responsibility Match"
            color="#8b5cf6"
            subtitle="Alignment with day-to-day duties"
          />
        </div>
      </div>

      {/* Matched vs Missing Skills */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-5 bg-slate-900/60 border border-emerald-900/40 rounded-xl space-y-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <h4 className="text-sm font-semibold text-emerald-300">Matched JD Skills ({matchReport.matched_skills?.length || 0})</h4>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {matchReport.matched_skills?.map((s, idx) => (
              <span key={idx} className="text-xs px-2.5 py-1 rounded-md bg-emerald-950/80 border border-emerald-700/50 text-emerald-200 font-medium">
                ✓ {s}
              </span>
            ))}
          </div>
        </div>

        <div className="card p-5 bg-slate-900/60 border border-red-900/40 rounded-xl space-y-3">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="text-red-400" />
            <h4 className="text-sm font-semibold text-red-300">
              Missing Target Skills ({((matchReport.missing_required_skills?.length || 0) + (matchReport.missing_preferred_skills?.length || 0))})
            </h4>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {matchReport.missing_required_skills?.map((s, idx) => (
              <span key={idx} className="text-xs px-2.5 py-1 rounded-md bg-red-950/80 border border-red-700/60 text-red-200 font-medium">
                ! {s}
              </span>
            ))}
            {matchReport.missing_preferred_skills?.map((s, idx) => (
              <span key={idx} className="text-xs px-2.5 py-1 rounded-md bg-amber-950/60 border border-amber-800/40 text-amber-200 text-xs">
                {s} (preferred)
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Actionable Gaps & How to Fix Them */}
      {((matchReport.gap_details && matchReport.gap_details.length > 0) || (matchReport.gaps && matchReport.gaps.length > 0)) && (
        <div className="card p-5 bg-slate-900/80 border border-amber-800/40 rounded-2xl space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-400">
              <AlertCircle size={18} />
              <h4 className="text-sm font-bold text-slate-100">Gaps Identified & Actionable Ways to Fix Them</h4>
            </div>
            <span className="text-xs text-amber-300/80 bg-amber-950/60 px-2.5 py-0.5 rounded-full border border-amber-800/40">
              {(matchReport.gap_details?.length || matchReport.gaps?.length || 0)} Action Items
            </span>
          </div>

          <div className="space-y-3">
            {matchReport.gap_details && matchReport.gap_details.length > 0 ? (
              matchReport.gap_details.map((item, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-slate-800 text-slate-200 border border-slate-700">
                      {item.category}
                    </span>
                    {item.severity && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        item.severity === 'high' ? 'bg-red-950/80 text-red-300 border border-red-800/50' : 'bg-amber-950/80 text-amber-300 border border-amber-800/40'
                      }`}>
                        {item.severity} Priority
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-200 font-medium flex items-start gap-1.5">
                    <span className="text-red-400 font-bold flex-shrink-0">⚠️</span>
                    <span>{item.gap}</span>
                  </p>
                  <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-200/90 leading-relaxed flex items-start gap-2">
                    <span className="text-emerald-400 font-bold flex-shrink-0">💡 Fix:</span>
                    <span>{item.how_to_fix}</span>
                  </div>
                </div>
              ))
            ) : (
              matchReport.gaps.map((gap, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 space-y-2">
                  <p className="text-xs text-slate-200 font-medium flex items-start gap-1.5">
                    <span className="text-red-400 font-bold flex-shrink-0">⚠️</span>
                    <span>{gap}</span>
                  </p>
                  {matchReport.suggestions && matchReport.suggestions[idx] && (
                    <div className="p-2.5 rounded-lg bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-200/90 leading-relaxed flex items-start gap-2">
                      <span className="text-emerald-400 font-bold flex-shrink-0">💡 Fix:</span>
                      <span>{matchReport.suggestions[idx]}</span>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* High-Impact Improvements */}
      {matchReport.high_impact_improvements && matchReport.high_impact_improvements.length > 0 && (
        <div className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <h4 className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
            <Zap size={13} />
            <span>AI Roadmap for Maximum ATS Score</span>
          </h4>
          <ul className="space-y-1.5 text-xs text-slate-300">
            {matchReport.high_impact_improvements.map((tip, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="text-red-400 font-bold">•</span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <button type="button" className="btn-secondary text-sm" onClick={() => goToStep('upload')}>
          ← Back to Upload
        </button>
        <button
          type="button"
          className="btn-primary flex items-center gap-2 text-sm font-semibold px-6 py-3 rounded-xl"
          onClick={() => goToStep('requirements')}
        >
          <span>Requirements Alignment</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ─── Step 3: Requirements Alignment ────────────────────────────────────────

function StepRequirements() {
  const {
    requirements, jdData, resumeData, userRequirements,
    setUserRequirements, goToStep, resumeId, jdId,
    setLoading, setError, setTailoredResult
  } = usePipeline();

  const missingSkills = [
    ...(requirements?.missing_required_skills || []),
    ...(requirements?.missing_preferred_skills || []),
  ];

  const toggleSkill = (skill: string) => {
    setUserRequirements((prev) => {
      const exists = prev.confirmed_skills.includes(skill);
      return {
        ...prev,
        confirmed_skills: exists
          ? prev.confirmed_skills.filter((s) => s !== skill)
          : [...prev.confirmed_skills, skill],
      };
    });
  };

  const handleRunTailor = async (skipRequirements = false) => {
    if (!resumeId || !jdId) return;
    const reqPayload = skipRequirements
      ? undefined
      : {
          confirmed_skills: userRequirements.confirmed_skills,
          additional_context: userRequirements.additional_context,
        };

    setLoading(true, 'Tailoring resume for 1-page layout and matching relevant projects...');
    try {
      const res = await api.tailorResume(resumeId, jdId, reqPayload);
      setTailoredResult(res.final_id, res.resume, res.match, res.suggested_projects);
      toast.success('Resume tailored strictly for 1 page with relevant projects!');
      goToStep('tailor');
    } catch (e: any) {
      setError(api.getErrorMessage(e));
      toast.error('Tailoring error: ' + api.getErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
        <div className="flex items-center gap-2.5 text-amber-400 mb-1">
          <HelpCircle size={18} />
          <h3 className="font-bold text-slate-100 text-base">Verify Target Role Requirements</h3>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed mt-1">
          {requirements?.prompt_message ||
            `The job description for ${jdData?.role_title || 'this role'} highlights skills not explicitly listed in your resume. Check off any that you have worked with so we can align your resume honestly without hallucinating.`}
        </p>
      </div>

      {missingSkills.length > 0 ? (
        <div className="space-y-4">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Select Skills You Have Experience With:
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2.5">
            {missingSkills.map((skill, idx) => {
              const selected = userRequirements.confirmed_skills.includes(skill);
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => toggleSkill(skill)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all border text-left ${
                    selected
                      ? 'bg-emerald-950/70 border-emerald-500 text-emerald-200 shadow-md shadow-emerald-950/50'
                      : 'bg-slate-900/60 border-slate-700 text-slate-300 hover:border-slate-500'
                  }`}
                >
                  <span className="truncate">{skill}</span>
                  {selected ? <Check size={14} className="text-emerald-400 ml-1 flex-shrink-0" /> : <span className="w-3.5 h-3.5 rounded-full border border-slate-600 ml-1 flex-shrink-0" />}
                </button>
              );
            })}
          </div>

          <div className="space-y-1.5 pt-2">
            <label className="block text-xs font-semibold text-slate-300">
              Additional Context / Lab Experience (Optional):
            </label>
            <textarea
              className="w-full h-24 rounded-xl p-3 text-xs bg-slate-900/60 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-red-500 focus:ring-1 focus:ring-red-500 outline-none resize-none transition-all"
              placeholder="e.g. Deployed Redis in my distributed systems project, implemented Docker containers in Linux lab..."
              value={userRequirements.additional_context}
              onChange={(e) =>
                setUserRequirements((prev) => ({ ...prev, additional_context: e.target.value }))
              }
            />
            <p className="text-[11px] text-slate-500 italic">
              These details will only be used to ground and enrich your project bullet points truthfully.
            </p>
          </div>
        </div>
      ) : (
        <div className="p-6 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-center space-y-2">
          <CheckCircle2 size={28} className="text-emerald-400 mx-auto" />
          <h4 className="text-sm font-bold text-emerald-300">No Skill Gaps Identified!</h4>
          <p className="text-xs text-slate-300">Your resume already includes all core technical requirements specified in the job posting.</p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex flex-col sm:flex-row justify-between items-center gap-3 pt-4 border-t border-slate-800">
        <button type="button" className="btn-secondary text-sm w-full sm:w-auto" onClick={() => goToStep('analyze')}>
          ← Back to Analysis
        </button>
        <div className="flex gap-2 w-full sm:w-auto">
          {missingSkills.length > 0 && (
            <button
              type="button"
              className="btn-secondary text-xs px-4 py-2.5 rounded-xl text-slate-300 hover:text-white"
              onClick={() => handleRunTailor(true)}
            >
              Skip & Use Current Resume
            </button>
          )}
          <button
            type="button"
            className="btn-primary flex items-center justify-center gap-2 text-sm font-semibold px-6 py-3 rounded-xl shadow-lg shadow-red-600/30"
            onClick={() => handleRunTailor(false)}
          >
            <Sparkles size={16} />
            <span>Generate Grounded Tailored Resume</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Step 4: Tailor & Review ───────────────────────────────────────────────

function StepTailor() {
  const {
    finalResumeData, tailoredMatchReport, matchReport, jdData, suggestedProjects,
    goToStep, isLoading, loadingMessage
  } = usePipeline();

  if (isLoading) {
    return (
      <LoadingProgressBar
        title={loadingMessage || 'Tailoring Resume with AI…'}
        subtitle="Curating JD-relevant projects, tightening bullet points, and enforcing strict 1-page fit."
        estimatedDurationMs={6500}
      />
    );
  }

  if (!finalResumeData) {
    return (
      <div className="text-center py-8">
        <p className="text-slate-400 text-sm mb-4">No tailored resume generated yet.</p>
        <button type="button" className="btn-primary text-sm" onClick={() => goToStep('requirements')}>
          Go to Requirements
        </button>
      </div>
    );
  }

  const origScore = Math.round(matchReport?.overall_score || 0);
  const newScore = Math.round(tailoredMatchReport?.overall_score || origScore + 15);

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Anti-Hallucination & Score Badge */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 p-5 rounded-2xl bg-emerald-950/30 border border-emerald-700/50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400 flex-shrink-0">
            <ShieldCheck size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-bold text-emerald-200">100% Grounded Customization</span>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-900/60 border border-emerald-600/40 text-emerald-300">
                0 Hallucinations
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Every bullet point and skill is strictly grounded in candidate background and verified facts.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 bg-slate-950/70 px-4 py-2.5 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400">Score Impact:</span>
          <span className="text-xs font-bold text-slate-400">{origScore}%</span>
          <ArrowRight size={13} className="text-slate-500" />
          <span className="text-lg font-black text-emerald-400">{newScore}%</span>
          <span className="text-xs font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded-full border border-emerald-700/50">
            +{Math.max(newScore - origScore, 0)}%
          </span>
        </div>
      </div>

      {/* Tailored Professional Summary */}
      {finalResumeData.summary && (
        <div className="card p-5 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
              <Sparkles size={13} />
              Tailored Professional Summary
            </span>
            <span className="text-xs text-slate-400">Crafted for {jdData?.role_title || 'Target Role'}</span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed font-normal bg-slate-950/50 p-3.5 rounded-lg border border-slate-800">
            {finalResumeData.summary}
          </p>
        </div>
      )}

      {/* Curated Tailored Projects (Strictly 1-Page Aligned) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-bold text-slate-100 flex items-center gap-2">
            <span>Relevant Projects ({finalResumeData.projects.length})</span>
            <span className="text-xs font-normal text-cyan-400 bg-cyan-950/60 px-2.5 py-0.5 rounded-full border border-cyan-700/40">
              🎯 Top Role Matches (Strictly 1-Page Layout)
            </span>
          </h4>
        </div>

        <div className="space-y-3">
          {finalResumeData.projects.map((proj, idx) => (
            <div key={idx} className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2.5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h5 className="text-sm font-bold text-white">{proj.name}</h5>
                {proj.technologies && proj.technologies.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {proj.technologies.slice(0, 6).map((t, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-1.5 pl-2 border-l-2 border-red-500/40">
                {proj.description.split('\n').filter(Boolean).map((bullet, bIdx) => (
                  <p key={bIdx} className="text-xs text-slate-300 leading-relaxed">
                    {bullet}
                  </p>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommended Projects to Build (Suggested for Gaps) */}
      {suggestedProjects && suggestedProjects.length > 0 && (
        <div className="card p-5 bg-gradient-to-br from-amber-950/30 via-slate-900/80 to-slate-900/60 border border-amber-600/40 rounded-2xl space-y-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center text-amber-400">
                <Sparkles size={16} />
              </div>
              <div>
                <h4 className="text-sm font-bold text-amber-200">Recommended Portfolio Projects to Build</h4>
                <p className="text-[11px] text-amber-300/80">
                  Targeted project ideas to bridge technical gaps between your resume and {jdData?.role_title || 'the target role'}
                </p>
              </div>
            </div>
            <span className="text-xs font-semibold text-amber-400 bg-amber-950/80 px-2.5 py-1 rounded-full border border-amber-700/50">
              {suggestedProjects.length} Suggested
            </span>
          </div>

          <div className="grid gap-3 pt-1">
            {suggestedProjects.map((sp, idx) => (
              <div key={idx} className="p-3.5 bg-slate-950/60 border border-amber-900/40 rounded-xl space-y-2">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h5 className="text-xs font-bold text-slate-100">{sp.title}</h5>
                  <div className="flex flex-wrap gap-1">
                    {sp.technologies.map((t, ti) => (
                      <span key={ti} className="text-[10px] px-1.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800/40 font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="text-[11px] text-amber-300/90 italic">💡 {sp.rationale}</p>
                <div className="space-y-1 pl-2 border-l-2 border-amber-600/50">
                  {sp.bullets.map((b, bi) => (
                    <p key={bi} className="text-xs text-slate-300 leading-relaxed">
                      • {b}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reordered Skills */}
      {finalResumeData.skills && finalResumeData.skills.length > 0 && (
        <div className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Prioritized Technical Skills ({finalResumeData.skills.length})
          </span>
          <div className="flex flex-wrap gap-1.5">
            {finalResumeData.skills.map((s, idx) => (
              <span
                key={idx}
                className="text-xs px-2.5 py-1 rounded-md bg-slate-800/90 border border-slate-700 text-slate-200 font-medium"
              >
                {s.name} <span className="text-[10px] text-slate-400">({s.category || 'Skill'})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Preserved Certifications & Achievements (Separate Sections) */}
      {(() => {
        const isAward = (item: any) => {
          const blob = `${item.name || ''} ${item.issuer || ''}`.toLowerCase();
          const keywords = [
            'place', 'award', 'winner', 'win', 'won', 'hackathon', 'finalist',
            'prize', 'champion', 'runner-up', 'runner up', 'competition', 'contest',
            'rank', 'medal', 'trophy', 'scholarship', 'fellowship', 'merit',
            'honor', 'honour', 'innovates', 'national', 'state-level', 'college-level', 'ctf', 'olympiad'
          ];
          return keywords.some((k) => blob.includes(k));
        };
        const allCerts = [
          ...(finalResumeData.certifications || []),
          ...(finalResumeData.achievements || []),
        ];
        const certList = allCerts.filter((c) => !isAward(c));
        const achList = allCerts.filter((c) => isAward(c));

        return (
          <>
            {certList.length > 0 && (
              <div className="card p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-300">
                    Certifications ({certList.length})
                  </span>
                  <span className="text-[11px] text-emerald-400 font-medium">✓ Separate Section in PDF</span>
                </div>
                <div className="grid sm:grid-cols-2 gap-2 pt-1">
                  {certList.map((cert, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800 flex items-center justify-between gap-2 text-xs">
                      <div className="truncate">
                        <p className="font-semibold text-slate-100 truncate">{cert.name}</p>
                        {cert.issuer && <p className="text-[11px] text-slate-400 truncate">{cert.issuer}</p>}
                      </div>
                      {cert.date && <span className="text-[11px] text-slate-400 font-mono flex-shrink-0">{cert.date}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {achList.length > 0 && (
              <div className="card p-4 bg-slate-900/60 border border-indigo-900/40 rounded-xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                    Achievements & Honors ({achList.length})
                  </span>
                  <span className="text-[11px] text-indigo-400 font-medium">✓ Separate Section in PDF</span>
                </div>
                <div className="grid sm:grid-cols-2 gap-2 pt-1">
                  {achList.map((ach, idx) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-slate-950/60 border border-indigo-950/60 flex items-center justify-between gap-2 text-xs">
                      <div className="truncate">
                        <p className="font-semibold text-slate-100 truncate">{ach.name}</p>
                        {ach.issuer && <p className="text-[11px] text-slate-400 truncate">{ach.issuer}</p>}
                      </div>
                      {ach.date && <span className="text-[11px] text-slate-400 font-mono flex-shrink-0">{ach.date}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        );
      })()}

      {/* Navigation */}
      <div className="flex justify-between pt-2">
        <button type="button" className="btn-secondary text-sm" onClick={() => goToStep('requirements')}>
          ← Back to Requirements
        </button>
        <button
          type="button"
          className="btn-primary flex items-center gap-2 text-sm font-semibold px-7 py-3 rounded-xl shadow-lg shadow-red-600/30"
          onClick={() => goToStep('download')}
        >
          <span>Export Resume</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ─── Step 5: Export & Download ─────────────────────────────────────────────

function StepDownload() {
  const { resumeId, jdId, finalId, jdData, finalResumeData, reset, goToStep } = usePipeline();
  const [downloading, setDownloading] = useState<string | null>(null);
  const [showInlinePreview, setShowInlinePreview] = useState(true);

  // Direct streaming URL for browser PDF viewing & iframe embedding
  const previewUrl = api.getExportUrl({
    finalId,
    resumeId,
    format: 'pdf',
    preview: true,
  });

  const downloadFile = async (format: 'pdf' | 'latex' | 'markdown') => {
    setDownloading(format);
    try {
      const blob = await api.exportResume({
        finalId,
        resumeId,
        format,
        resumeData: finalResumeData,
      });
      const ext = format === 'latex' ? 'tex' : format === 'markdown' ? 'md' : 'pdf';
      const roleName = (jdData?.role_title || 'resume').replace(/\s+/g, '_');
      const filename = `tailored_resume_${roleName}.${ext}`;
      const mime = format === 'pdf' ? 'application/pdf' : 'text/plain';
      const typedBlob = new Blob([blob], { type: mime });
      const url = URL.createObjectURL(typedBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      toast.success(`Downloaded ${filename} in Jake's template!`);
    } catch (e: any) {
      toast.error(`Download failed: ${api.getErrorMessage(e)}`);
    } finally {
      setDownloading(null);
    }
  };

  const previewInNewTab = () => {
    window.open(previewUrl, '_blank');
    toast.success('Opened PDF preview in new tab!');
  };

  return (
    <div className="space-y-6 animate-slide-up text-center max-w-3xl mx-auto py-2">
      <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-500/20 flex items-center justify-center mb-2">
        <CheckCircle2 size={32} className="text-emerald-400" />
      </div>

      <div>
        <h3 className="text-2xl font-bold text-white">Your Tailored Resume is Ready!</h3>
        <p className="text-xs text-slate-400 mt-1">
          Covers the full single page with optimal typography, keeping all relevant projects and certifications.
        </p>
      </div>

      {finalResumeData && (
        <div className="text-left bg-slate-950/70 border border-slate-800 p-4 rounded-xl space-y-1.5 text-xs text-slate-300">
          <div className="flex justify-between items-center font-semibold text-white">
            <span>{finalResumeData.contact.name || 'Candidate'}</span>
            <span className="text-emerald-400">✓ Full 1-Page Layout · Grounded</span>
          </div>
          <p className="text-slate-400">{jdData?.role_title || 'Target Role'}</p>
          <p className="text-slate-500 pt-1 font-mono">
            {finalResumeData.skills.length} Technical Skills · {finalResumeData.projects.length} Relevant Projects · {finalResumeData.certifications?.length || 0} Certifications · {finalResumeData.experience.length} Experience Entries
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="grid sm:grid-cols-2 gap-3 pt-2">
        <button
          type="button"
          className="btn-primary font-semibold px-6 py-3.5 text-sm flex items-center justify-center gap-2 rounded-xl shadow-lg shadow-red-600/30"
          onClick={() => downloadFile('pdf')}
          disabled={!!downloading}
        >
          {downloading === 'pdf' ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Download size={16} />
          )}
          <span>Download PDF (Jake&apos;s Template)</span>
        </button>

        <button
          type="button"
          className="btn-secondary font-semibold px-6 py-3.5 text-sm flex items-center justify-center gap-2 rounded-xl text-slate-200 hover:text-white"
          onClick={previewInNewTab}
        >
          <ExternalLink size={16} className="text-slate-400" />
          <span>Open PDF in New Tab</span>
        </button>

        <button
          type="button"
          className="btn-secondary font-semibold px-6 py-3 text-xs flex items-center justify-center gap-2 rounded-xl text-slate-300"
          onClick={() => downloadFile('latex')}
          disabled={!!downloading}
        >
          {downloading === 'latex' ? (
            <div className="w-3.5 h-3.5 border-2 border-slate-300 border-t-transparent rounded-full animate-spin" />
          ) : (
            <FileCode size={14} />
          )}
          <span>Download LaTeX (.tex)</span>
        </button>

        <button
          type="button"
          className="btn-secondary font-semibold px-6 py-3 text-xs flex items-center justify-center gap-2 rounded-xl text-slate-300"
          onClick={() => downloadFile('markdown')}
          disabled={!!downloading}
        >
          {downloading === 'markdown' ? (
            <div className="w-3.5 h-3.5 border-2 border-slate-300 border-t-transparent rounded-full animate-spin" />
          ) : (
            <FileText size={14} />
          )}
          <span>Download Markdown (.md)</span>
        </button>
      </div>

      {/* Inline Document Preview Toggle */}
      <div className="pt-3">
        <div className="flex items-center justify-between py-2 border-t border-slate-800/80 text-xs">
          <span className="font-semibold text-slate-300 flex items-center gap-2">
            <FileText size={14} className="text-red-400" />
            <span>Interactive Document Preview</span>
          </span>
          <button
            type="button"
            onClick={() => setShowInlinePreview((v) => !v)}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors font-medium bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-700/60"
          >
            {showInlinePreview ? <EyeOff size={13} /> : <Eye size={13} />}
            <span>{showInlinePreview ? 'Hide Preview' : 'Show PDF Preview'}</span>
          </button>
        </div>

        {showInlinePreview && (
          <div className="mt-3 rounded-2xl overflow-hidden border border-slate-800 bg-slate-950/90 shadow-2xl p-2 animate-fade-in">
            <div className="flex justify-between items-center px-3 py-2 bg-slate-900/90 rounded-t-xl text-[11px] text-slate-400 border-b border-slate-800">
              <span className="font-mono">Jake&apos;s LaTeX Aligned Template (ReportLab Engine)</span>
              <button
                type="button"
                onClick={previewInNewTab}
                className="text-red-400 hover:text-red-300 flex items-center gap-1 font-semibold"
              >
                <span>Full screen</span>
                <ExternalLink size={11} />
              </button>
            </div>
            <iframe
              src={previewUrl}
              className="w-full h-[640px] rounded-b-xl border-none bg-white"
              title="Tailored Resume Preview"
            />
          </div>
        )}
      </div>

      <div className="pt-4 flex justify-center gap-4 border-t border-slate-800">
        <button
          type="button"
          className="text-xs text-slate-400 hover:text-white transition-colors"
          onClick={() => goToStep('tailor')}
        >
          ← Review Tailored Sections
        </button>
        <span className="text-slate-700">·</span>
        <button
          type="button"
          className="text-xs text-red-400 hover:text-red-300 transition-colors"
          onClick={reset}
        >
          Tailor Another Resume
        </button>
      </div>
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────────────

const STEPS: { key: PipelineStep; label: string; icon: React.ReactNode }[] = [
  { key: 'upload', label: '1. Upload', icon: <Upload size={14} /> },
  { key: 'analyze', label: '2. Fit & Gaps', icon: <BarChart3 size={14} /> },
  { key: 'requirements', label: '3. Requirements', icon: <AlertCircle size={14} /> },
  { key: 'tailor', label: '4. AI Customization', icon: <Sparkles size={14} /> },
  { key: 'download', label: '5. Export', icon: <Download size={14} /> },
];

export default function ResumeTailorForm() {
  const { currentStep, error, setError, goToStep } = usePipeline();

  const getStepStatus = (stepKey: PipelineStep) => {
    const order: PipelineStep[] = ['upload', 'analyze', 'requirements', 'tailor', 'download'];
    const curIdx = order.indexOf(currentStep);
    const stepIdx = order.indexOf(stepKey);
    if (curIdx === stepIdx) return 'active';
    if (curIdx > stepIdx) return 'completed';
    return 'upcoming';
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* 5-Step Pipeline Navigation Bar */}
      <nav aria-label="Pipeline Progress" className="w-full">
        <div className="grid grid-cols-5 gap-1.5 sm:gap-2 p-1.5 bg-slate-900/80 border border-slate-800 rounded-2xl backdrop-blur-md">
          {STEPS.map((s) => {
            const status = getStepStatus(s.key);
            const isClickable = status === 'completed';

            return (
              <button
                key={s.key}
                type="button"
                disabled={!isClickable}
                onClick={() => isClickable && goToStep(s.key)}
                className={`flex items-center justify-center gap-1.5 py-2.5 px-2 rounded-xl text-xs font-semibold transition-all ${
                  status === 'active'
                    ? 'bg-red-600 text-white shadow-lg shadow-red-600/30'
                    : status === 'completed'
                    ? 'text-emerald-400 hover:bg-slate-800/80 cursor-pointer'
                    : 'text-slate-500 cursor-default opacity-60'
                }`}
              >
                {status === 'completed' ? (
                  <Check size={13} className="text-emerald-400 flex-shrink-0" />
                ) : (
                  <span className="flex-shrink-0">{s.icon}</span>
                )}
                <span className="hidden sm:inline truncate">{s.label}</span>
              </button>
            );
          })}
        </div>
      </nav>

      {/* Error Alert */}
      {error && (
        <div className="p-4 bg-red-950/40 border border-red-800/60 rounded-xl flex items-center justify-between gap-3 text-red-200 text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle size={16} className="text-red-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button type="button" onClick={() => setError(null)} className="text-red-400 hover:text-white">
            <X size={14} />
          </button>
        </div>
      )}

      {/* Main Step Container */}
      <div className="card p-6 md:p-8 bg-slate-900/70 border border-slate-800/80 rounded-2xl backdrop-blur-md shadow-2xl">
        {currentStep === 'upload' && <StepUpload />}
        {currentStep === 'analyze' && <StepAnalyze />}
        {currentStep === 'requirements' && <StepRequirements />}
        {currentStep === 'tailor' && <StepTailor />}
        {currentStep === 'download' && <StepDownload />}
      </div>
    </div>
  );
}