import type { NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { ArrowLeft, Sparkles } from 'lucide-react';
import ResumeTailorForm from '../components/ResumeTailorForm';

const Tool: NextPage = () => {
  return (
    <>
      <Head>
        <title>Tailor Your Resume — ResumeAI</title>
        <meta
          name="description"
          content="Upload your resume and a job description. Get an ATS-optimized, grounded tailored resume in seconds."
        />
      </Head>

      {/* Same dark canvas as the landing page for visual continuity */}
      <div className="bg-canvas">
        <div className="bg-grid" />
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
      </div>

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Top bar — back to landing */}
        <header className="sticky top-0 z-50 w-full px-6 py-3"
          style={{
            background: 'rgba(7,7,15,0.8)',
            backdropFilter: 'blur(24px) saturate(180%)',
            WebkitBackdropFilter: 'blur(24px) saturate(180%)',
            borderBottom: '1px solid rgba(255,46,46,0.1)',
          }}>
          <div className="max-w-5xl mx-auto flex items-center justify-between">
            <Link
              href="/"
              className="inline-flex items-center gap-2 text-xs font-semibold transition-colors duration-200"
              style={{ color: 'var(--text-secondary)' }}
            >
              <ArrowLeft size={14} />
              <span>Back to home</span>
            </Link>

            <div className="flex items-center gap-2.5">
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center"
                style={{
                  background: 'linear-gradient(135deg,#ff2e2e,#ff7a9a)',
                  boxShadow: '0 0 16px rgba(255,46,46,0.4)',
                }}
              >
                <Sparkles size={13} className="text-white" />
              </div>
              <span className="font-bold text-sm tracking-tight text-white">
                Resume<span className="glow-text-sm">AI</span>
              </span>
            </div>
          </div>
        </header>

        {/* The form — completely unchanged */}
        <main className="flex-1 px-4 py-8">
          <ResumeTailorForm />
        </main>
      </div>
    </>
  );
};

export default Tool;
