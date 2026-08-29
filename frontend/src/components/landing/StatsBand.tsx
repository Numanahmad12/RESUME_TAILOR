import { motion, useInView, useMotionValue, useTransform, animate, useReducedMotion } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import Reveal from './Reveal';

type Stat = { value: number; suffix: string; label: string };

const STATS: Stat[] = [
  { value: 8,  suffix: '',  label: 'Pipeline stages' },
  { value: 5,  suffix: '',  label: 'Sub-scores' },
  { value: 4,  suffix: '',  label: 'Export formats' },
  { value: 0,  suffix: '',  label: 'Hallucinations' },
];

function Counter({ to, suffix, active }: { to: number; suffix: string; active: boolean }) {
  const reduce = useReducedMotion();
  const mv = useMotionValue(0);
  const rounded = useTransform(mv, (v) => `${Math.round(v)}${suffix}`);
  const [display, setDisplay] = useState(`0${suffix}`);

  useEffect(() => {
    if (!active) return;
    if (reduce) {
      setDisplay(`${to}${suffix}`);
      return;
    }
    const controls = animate(mv, to, { duration: 1.5, ease: [0.16, 1, 0.3, 1] });
    const unsub = rounded.on('change', (v) => setDisplay(v));
    return () => {
      controls.stop();
      unsub();
    };
  }, [active, to, suffix, reduce, mv, rounded]);

  return <span>{display}</span>;
}

export default function StatsBand() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: '-15% 0px' });

  return (
    <section ref={ref} className="relative py-12 md:py-16">
      <div className="max-w-6xl mx-auto px-6">
        <Reveal>
          <div
            className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6 rounded-3xl px-6 py-8 md:px-10 md:py-10"
            style={{
              background:
                'linear-gradient(135deg, rgba(255,46,46,0.08), rgba(255,122,154,0.05))',
              border: '1px solid rgba(255,46,46,0.15)',
              boxShadow: '0 8px 32px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04)',
            }}
          >
            {STATS.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 12 }}
                animate={inView ? { opacity: 1, y: 0 } : {}}
                transition={{ delay: i * 0.1, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="text-center md:text-left relative"
              >
                <div
                  className="text-4xl md:text-5xl font-black mb-1 font-display"
                  style={{
                    color: '#ff2e2e',
                    letterSpacing: '-0.03em',
                  }}
                >
                  <Counter to={stat.value} suffix={stat.suffix} active={inView} />
                </div>
                <div
                  className="text-[11px] md:text-xs font-medium uppercase tracking-wider"
                  style={{ color: 'var(--text-muted)' }}
                >
                  {stat.label}
                </div>
                {i < STATS.length - 1 && (
                  <div
                    className="hidden md:block absolute right-0 top-1/2 -translate-y-1/2 h-10 w-px"
                    style={{ background: 'rgba(255,46,46,0.12)' }}
                  />
                )}
              </motion.div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
