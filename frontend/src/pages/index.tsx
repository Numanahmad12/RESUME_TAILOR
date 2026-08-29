import type { NextPage } from 'next';
import Head from 'next/head';
import dynamic from 'next/dynamic';

// Lazy-load the entire landing composition so the Three.js / GSAP chunks
// never enter the /tool route's bundle. The fallback is the page background.
const LandingPage = dynamic(() => import('../components/landing/LandingPage'), {
  ssr: true,
  loading: () => (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--bg-primary)' }}>
      <div className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin"
        style={{ borderColor: 'var(--accent)', borderTopColor: 'transparent' }} />
    </div>
  ),
});

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>ResumeAI — ATS-Safe, Grounded Resume Tailoring</title>
        <meta
          name="description"
          content="An 8-stage AI pipeline that scores, generates, validates, and renders a perfectly tailored resume for any job description — with zero hallucinations."
        />
        <meta property="og:title" content="ResumeAI — ATS-Safe Resume Tailoring" />
        <meta
          property="og:description"
          content="Upload your resume and a job description. Get a JD-aligned, ATS-safe, fully grounded tailored resume in seconds."
        />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </Head>
      <LandingPage />
    </>
  );
};

export default Home;
