/**
 * Zustand store for the full resume tailoring pipeline state.
 */
import { create } from 'zustand';
import type {
  ResumeData, JdData, MatchReport, PatchAction,
} from '../utils/api';

export type PipelineStep = 'upload' | 'analyze' | 'review' | 'download';

interface PipelineState {
  // Step tracking
  currentStep: PipelineStep;

  // Upload state
  resumeFile: File | null;
  jdFile: File | null;
  jdText: string;

  // Backend IDs
  resumeId: string | null;
  jdId: string | null;
  generationId: string | null;
  finalId: string | null;

  // Data
  resumeData: ResumeData | null;
  jdData: JdData | null;
  matchReport: MatchReport | null;
  patches: PatchAction[];
  finalResumeData: ResumeData | null;

  // UI state
  isLoading: boolean;
  loadingMessage: string;
  error: string | null;

  // Actions
  setResumeFile: (file: File | null) => void;
  setJdFile: (file: File | null) => void;
  setJdText: (text: string) => void;
  setResumeUploaded: (id: string, data: ResumeData) => void;
  setJdUploaded: (id: string, data: JdData) => void;
  setMatchReport: (report: MatchReport) => void;
  setPatches: (generationId: string, patches: PatchAction[]) => void;
  setFinalResume: (finalId: string, data: ResumeData) => void;
  setLoading: (loading: boolean, message?: string) => void;
  setError: (error: string | null) => void;
  goToStep: (step: PipelineStep) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 'upload' as PipelineStep,
  resumeFile: null,
  jdFile: null,
  jdText: '',
  resumeId: null,
  jdId: null,
  generationId: null,
  finalId: null,
  resumeData: null,
  jdData: null,
  matchReport: null,
  patches: [],
  finalResumeData: null,
  isLoading: false,
  loadingMessage: '',
  error: null,
};

export const usePipeline = create<PipelineState>((set) => ({
  ...initialState,

  setResumeFile: (file) => set({ resumeFile: file, error: null }),
  setJdFile: (file) => set({ jdFile: file, error: null }),
  setJdText: (text) => set({ jdText: text }),
  setResumeUploaded: (id, data) => set({ resumeId: id, resumeData: data }),
  setJdUploaded: (id, data) => set({ jdId: id, jdData: data }),
  setMatchReport: (report) => set({ matchReport: report }),
  setPatches: (generationId, patches) => set({ generationId, patches }),
  setFinalResume: (finalId, data) => set({ finalId, finalResumeData: data }),
  setLoading: (loading, message = '') => set({ isLoading: loading, loadingMessage: message }),
  setError: (error) => set({ error, isLoading: false }),
  goToStep: (step) => set({ currentStep: step }),
  reset: () => set(initialState),
}));
