/**
 * Zustand store for the full resume tailoring pipeline state.
 */
import { create } from 'zustand';
import type {
  ResumeData, JdData, MatchReport, RequirementsCheckResult, UserRequirements, ProjectSuggestion,
} from '../utils/api';

export type PipelineStep = 'upload' | 'analyze' | 'requirements' | 'tailor' | 'download';

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
  finalId: string | null;

  // Data
  resumeData: ResumeData | null;
  jdData: JdData | null;
  matchReport: MatchReport | null;
  tailoredMatchReport: MatchReport | null;
  requirements: RequirementsCheckResult | null;
  userRequirements: UserRequirements;
  finalResumeData: ResumeData | null;
  suggestedProjects: ProjectSuggestion[];

  // UI state
  isLoading: boolean;
  loadingMessage: string;
  generationAttempted: boolean;
  error: string | null;

  // Actions
  setResumeFile: (file: File | null) => void;
  setJdFile: (file: File | null) => void;
  setJdText: (text: string) => void;
  setResumeUploaded: (id: string, data: ResumeData) => void;
  setJdUploaded: (id: string, data: JdData) => void;
  setMatchReport: (report: MatchReport) => void;
  setRequirements: (reqs: RequirementsCheckResult) => void;
  setUserRequirements: (reqs: UserRequirements | ((prev: UserRequirements) => UserRequirements)) => void;
  setTailoredResult: (id: string, data: ResumeData, newMatch?: MatchReport, suggestedProjects?: ProjectSuggestion[]) => void;
  setLoading: (loading: boolean, message?: string) => void;
  setError: (error: string | null) => void;
  setGenerationAttempted: (attempted: boolean) => void;
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
  finalId: null,
  resumeData: null,
  jdData: null,
  matchReport: null,
  tailoredMatchReport: null,
  requirements: null,
  userRequirements: { confirmed_skills: [], additional_context: '' },
  finalResumeData: null,
  suggestedProjects: [] as ProjectSuggestion[],
  isLoading: false,
  loadingMessage: '',
  generationAttempted: false,
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
  setRequirements: (reqs) => set({ requirements: reqs }),
  setUserRequirements: (reqs) => set((state) => ({
    userRequirements: typeof reqs === 'function' ? reqs(state.userRequirements) : reqs,
  })),
  setTailoredResult: (id, data, newMatch, suggestedProjects) => set({
    finalId: id,
    finalResumeData: data,
    tailoredMatchReport: newMatch || null,
    suggestedProjects: suggestedProjects || [],
  }),
  setLoading: (loading, message = '') => set({ isLoading: loading, loadingMessage: message }),
  setError: (error) => set({ error, isLoading: false }),
  setGenerationAttempted: (attempted: boolean) => set({ generationAttempted: attempted }),
  goToStep: (step) => set({ currentStep: step }),
  reset: () => set(initialState),
}));

