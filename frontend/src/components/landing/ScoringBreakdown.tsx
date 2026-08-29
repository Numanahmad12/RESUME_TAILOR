import { motion, useInView, useReducedMotion } from 'framer-motion';
import { useRef } from 'react';
import Reveal from './Reveal';

type SubScore = { label: string; value: number; color: string; hint: string };

const SUB_SCORES: SubScore[] = [
  { label: 'Keyword Coverage',  value: 0.82, color: '#ff2e2e', hint: '35% weight' },
  { label: 'Experience Fit',    value: 0.74, color: '#e02626', hint: '25% weight' },
  { label: 'Responsibility Match', value: 0.69, color: '#ff5c8a', hint: '20% weight' },
  { label: 'Impact Metrics',    value: 0.55, color: '#ff7a9a', hint: '10% weight' },
  { label: 'ATS Formatting',    value: 0.92, color: '#10b981', hint: '10% weight' },
];

/**
 * Animated radial bars. Each bar fills from 0 to its value when in view.
 * Pure SVG — no chart library — so it stays small and themeable.
 */
export default function ScoringBreakdown() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: '-15% 0px' });
  const reduce = useReducedMotion();

  return (
    <section className="py-20 md:py-24" style={{ background: 'linear-gradient(180deg, transparent, rgba(255,46,46,0.03), transparent)' }}>
      <div ref={ref} className="max-w-6xl mx-auto px-6">
        <Reveal className="text-center mb-14">
          <p
            className="inline-block text-xs font-bold uppercase tracking-widest mb-3 px-3 py-1 rounded-full"
            style={{
              background: 'rgba(255,122,154,0.10)',
              border: '1px solid rgba(255,122,154,0.25)',
              color: '#ff7a9a',
            }}
          >
            Scoring
          </p>
          <h2
            className="text-4xl md:text-5xl font-black mb-4 tracking-tight"
            style={{ letterSpacing: '-0.03em' }}
          >
            Five sub-scores.{' '}
            <span className="text-gradient">One verdict.</span>
          </h2>
          <p className="text-base max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            A weighted breakdown shows you exactly where the resume matches the JD — and
            where the gaps are. No single-number black box.
          </p>
        </Reveal>

        <div className="grid sm:grid-cols-2 md:grid-cols-5 gap-5">
          {SUB_SCORES.map((s, i) => (
            <RadialBar key={s.label} score={s} index={i} active={inView} reduce={!!reduce} />
          ))}
        </div>

        <Reveal delay={0.3} className="mt-10 text-center">
          <div
            className="inline-flex items-center gap-3 px-5 py-3 rounded-2xl"
            style={{
              background: 'rgba(15,15,30,0.7)',
              border: '1px solid rgba(255,46,46,0.15)',
            }}
          >
            <div className="text-3xl font-black" style={{ color: '#ff7a7a' }}>78.4</div>
            <div className="text-left">
              <div className="text-[10px] uppercase tracking-widest font-semibold" style={{ color: 'var(--text-muted)' }}>
                Overall
              </div>
              <div className="text-sm font-bold text-white">Strong Fit</div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function RadialBar({
  score,
  index,
  active,
  reduce,
}: {
  score: SubScore;
  index: number;
  active: boolean;
  reduce: boolean;
}) {
  const SIZE = 120;
  const STROKE = 10;
  const RADIUS = (SIZE - STROKE) / 2;
  const CIRC = 2 * Math.PI * RADIUS;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-10% 0px' }}
      transition={{ delay: index * 0.12, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="p-5 rounded-2xl text-center"
      style={{
        background: 'rgba(15,15,30,0.6)',
        border: '1px solid rgba(255,46,46,0.12)',
        backdropFilter: 'blur(8px)',
        WebkitBackdropFilter: 'blur(8px)',
      }}
    >
      <div className="relative inline-block">
        <svg width={SIZE} height={SIZE} className="-rotate-90">
          {/* Track */}
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth={STROKE}
          />
          {/* Value */}
          <motion.circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={RADIUS}
            fill="none"
            stroke={score.color}
            strokeWidth={STROKE}
            strokeLinecap="round"
            strokeDasharray={CIRC}
            initial={{ strokeDashoffset: CIRC }}
            animate={active || reduce ? { strokeDashoffset: CIRC * (1 - score.value) } : {}}
            transition={{ delay: index * 0.12, duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            style={{
              filter: `drop-shadow(0 0 6px ${score.color}80)`,
            }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div
            className="text-2xl font-black"
            style={{ color: score.color }}
          >
            {Math.round(score.value * 100)}
          </div>
        </div>
      </div>
      <div className="mt-3">
        <div className="text-xs font-bold text-white mb-0.5">{score.label}</div>
        <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>
          {score.hint}
        </div>
      </div>
    </motion.div>
  );
}
