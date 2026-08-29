import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { ArrowRight, Github } from 'lucide-react';
import Reveal from './Reveal';

export default function CTASection() {
  const reduce = useReducedMotion();

  return (
    <section className="py-24 md:py-32 relative overflow-hidden">
      {/* Background glow */}
      <div
        aria-hidden
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(255,46,46,0.18) 0%, transparent 70%)',
        }}
      />

      <div className="relative max-w-4xl mx-auto px-6 text-center">
        <Reveal>
          <h2
            className="font-display text-5xl md:text-6xl lg:text-7xl mb-6 tracking-tight leading-[0.95]"
            style={{ letterSpacing: '-0.04em' }}
          >
            Ready to <span style={{ color: '#ff2e2e' }}>stand out?</span>
            <br />
            Start <span style={{ color: '#ff2e2e' }}>tailoring.</span>
          </h2>
        </Reveal>

        <Reveal delay={0.1}>
          <p
            className="text-base md:text-lg max-w-xl mx-auto mb-10"
            style={{ color: 'var(--text-secondary)' }}
          >
            Upload your resume and any job description. In seconds you get an honest ATS
            score, grounded patches, and a polished tailored resume — ready to download.
          </p>
        </Reveal>

        <Reveal delay={0.2}>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <motion.div
              whileHover={reduce ? undefined : { scale: 1.04 }}
              whileTap={reduce ? undefined : { scale: 0.97 }}
              transition={{ type: 'spring', stiffness: 300, damping: 18 }}
            >
              <Link
                href="/tool"
                className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-base font-bold transition-all duration-200"
                style={{
                  background: '#ff2e2e',
                  color: '#fff',
                  boxShadow:
                    '0 0 40px rgba(255,46,46,0.55), 0 12px 32px rgba(255,46,46,0.30)',
                }}
              >
                Tailor My Resume
                <ArrowRight size={18} />
              </Link>
            </motion.div>

            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-4 rounded-2xl text-sm font-semibold transition-all duration-200"
              style={{
                background: 'rgba(255,46,46,0.06)',
                border: '1px solid rgba(255,46,46,0.22)',
                color: '#ff7a7a',
              }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLElement).style.background = 'rgba(255,46,46,0.13)')
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLElement).style.background = 'rgba(255,46,46,0.06)')
              }
            >
              <Github size={16} />
              View on GitHub
            </a>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
