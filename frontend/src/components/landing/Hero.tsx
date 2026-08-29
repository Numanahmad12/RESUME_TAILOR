import dynamic from 'next/dynamic';
import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Play, Sparkles } from 'lucide-react';

// Lazy-load 3D canvas — keeps three.js out of the initial bundle and the /tool chunk.
const HeroScene = dynamic(() => import('./HeroScene'), {
  ssr: false,
  loading: () => <HeroFallback />,
});

const PIPELINE_PILLS = [
  'Parse', 'Analyze JD', 'Gap Score', 'Generate',
  'Validate', 'Review', 'Render', 'Export',
];

const stagger = {
  hidden: { opacity: 0 },
  visible: (i: number = 0) => ({
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.1 + i * 0.05 },
  }),
};

const child = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] },
  },
};

export default function Hero() {
  const reduce = useReducedMotion();

  return (
    <section className="relative pt-12 pb-16 md:pt-20 md:pb-24 overflow-hidden">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid md:grid-cols-2 gap-10 items-center">
          {/* ── Left: text ─────────────────────────────────────────── */}
          <motion.div
            initial="hidden"
            animate={reduce ? 'visible' : 'visible'}
            variants={stagger}
          >
            {/* Pill badge */}
            <motion.div
              variants={child}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-[11px] font-semibold mb-6"
              style={{
                background: 'rgba(255,46,46,0.10)',
                border: '1px solid rgba(255,46,46,0.30)',
                color: '#ff7a7a',
                boxShadow: '0 0 20px rgba(255,46,46,0.15)',
              }}
            >
              <span className="relative flex w-1.5 h-1.5">
                <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-75" />
                <span className="relative inline-flex w-1.5 h-1.5 rounded-full bg-emerald-400" />
              </span>
              AI-Powered · ATS-Safe · Hallucination-Free
            </motion.div>

            <motion.h1
              variants={child}
              className="font-display text-5xl md:text-6xl lg:text-7xl mb-6 leading-[0.95]"
              style={{ letterSpacing: '-0.04em' }}
            >
              <span style={{ color: '#ff2e2e' }}>Tailor</span>
              <span style={{ color: '#ffffff' }}> your resume</span>
              <br />
              <span style={{ color: '#ffffff' }}>with </span>
              <span style={{ color: '#ff2e2e' }}>precision.</span>
            </motion.h1>

            <motion.p
              variants={child}
              className="text-base md:text-lg max-w-xl mb-8 leading-relaxed"
              style={{ color: 'var(--text-secondary)' }}
            >
              Upload your resume and a job description. Our{' '}
              <span style={{ color: '#ff7a7a', fontWeight: 600 }}>8-stage AI pipeline</span>{' '}
              scores the match, generates grounded patches, validates every change, and exports a
              perfectly tailored document — with{' '}
              <span style={{ color: '#6ee7b7', fontWeight: 600 }}>zero hallucinations</span>.
            </motion.p>

            {/* CTAs */}
            <motion.div variants={child} className="flex flex-wrap items-center gap-3 mb-10">
              <Link
                href="/tool"
                className="group inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold transition-all duration-200"
                style={{
                  background: '#ff2e2e',
                  color: '#fff',
                  boxShadow: '0 0 28px rgba(255,46,46,0.45), 0 8px 24px rgba(255,46,46,0.25)',
                }}
              >
                Tailor My Resume
                <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
              </Link>
              <a
                href="#pipeline"
                className="inline-flex items-center gap-2 px-5 py-3.5 rounded-full text-sm font-semibold transition-all duration-200"
                style={{
                  background: 'transparent',
                  border: '1px solid rgba(255,255,255,0.15)',
                  color: '#fff',
                }}
                onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,46,46,0.6)')}
                onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.borderColor = 'rgba(255,255,255,0.15)')}
              >
                <Play size={13} />
                See How It Works
              </a>
            </motion.div>

            {/* Pipeline pills */}
            <motion.div variants={child} className="flex flex-wrap gap-1.5">
              {PIPELINE_PILLS.map((label, i) => (
                <motion.span
                  key={label}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 + i * 0.04, duration: 0.4 }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium"
                  style={{
                    background: 'rgba(15,15,30,0.7)',
                    border: '1px solid rgba(255,46,46,0.15)',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <span className="font-mono text-[9px] font-bold" style={{ color: '#4a4a6a' }}>
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  {label}
                </motion.span>
              ))}
            </motion.div>
          </motion.div>

          {/* ── Right: 3D canvas ───────────────────────────────────── */}
          <div className="relative h-[420px] md:h-[520px] lg:h-[560px]">
            {/* Glow halo behind canvas */}
            <div
              aria-hidden
              className="absolute inset-0 -z-10"
              style={{
                background:
                  'radial-gradient(circle at 50% 50%, var(--canvas-glow, rgba(255,46,46,0.18)) 0%, transparent 60%)',
                filter: 'blur(8px)',
              }}
            />
            <HeroScene />
          </div>
        </div>
      </div>
    </section>
  );
}

/** Static CSS-only fallback shown while the 3D chunk loads (or on mobile). */
function HeroFallback() {
  return (
    <div className="w-full h-full relative">
      <div
        className="absolute inset-0"
        style={{
          background:
            'radial-gradient(circle at 50% 40%, rgba(255,46,46,0.30), transparent 55%), radial-gradient(circle at 65% 60%, rgba(255,122,154,0.22), transparent 50%)',
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(circle, rgba(255,46,46,0.4) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
          opacity: 0.18,
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className="w-20 h-28 rounded-md animate-pulse"
          style={{
            background: 'linear-gradient(135deg, rgba(255,46,46,0.25), rgba(255,122,154,0.18))',
            border: '1px solid rgba(255,46,46,0.4)',
            boxShadow: '0 0 40px rgba(255,46,46,0.35)',
          }}
        />
      </div>
    </div>
  );
}
