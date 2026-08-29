import { FileSearch, ShieldCheck, FileOutput, RefreshCcw } from 'lucide-react';
import FeatureCard from './FeatureCard';
import Reveal from './Reveal';

const FEATURES = [
  {
    icon: FileSearch,
    title: 'Honest ATS Scoring',
    body: 'Five calibrated sub-scores — keyword coverage, experience fit, responsibility alignment, impact metrics, and formatting — give you an honest baseline before you tailor.',
    accent: '#ff5c8a',
    badge: 'Deterministic',
  },
  {
    icon: RefreshCcw,
    title: 'Grounded Patch Generation',
    body: 'Every change is schema-constrained and traceable. Summary rewrites, skill additions, and bullet upgrades are validated before they reach your resume — no fabrications.',
    accent: '#ff7a9a',
    badge: 'Validated',
  },
  {
    icon: FileOutput,
    title: 'DOCX & PDF Export',
    body: 'Download a clean, professional resume that passes ATS scanners. Preserves your original formatting, bullet density, and contact information while applying all patches.',
    accent: '#ff5c8a',
    badge: 'ATS-Safe',
  },
  {
    icon: ShieldCheck,
    title: 'Round-Trip Improvement',
    body: 'Upload the tailored resume again and the ATS score increases. Each pass compounds the match — the more you refine, the higher you rank.',
    accent: '#10b981',
    badge: 'Compounding',
  },
];

export default function FeatureGrid() {
  return (
    <section id="features" className="section-anchor py-20 md:py-28">
      <div className="max-w-6xl mx-auto px-6">
        <Reveal className="text-center mb-14">
          <p
            className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest mb-4"
            style={{ color: '#ff7a7a' }}
          >
            <span style={{ color: '#ff2e2e' }}>●</span> Features
          </p>
          <h2
            className="font-display text-4xl md:text-5xl mb-4"
            style={{ letterSpacing: '-0.04em' }}
          >
            Built for the{' '}
            <span style={{ color: '#ff2e2e' }}>real pipeline</span>
          </h2>
          <p className="text-base max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            No toy demos, no aspirational claims — these are the exact features that run every
            time you upload a resume and a job description.
          </p>
        </Reveal>

        <div className="grid sm:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => (
            <FeatureCard key={f.title} {...f} delay={i * 0.08} />
          ))}
        </div>
      </div>
    </section>
  );
}
