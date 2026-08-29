import { Upload, ScanSearch, FileOutput } from 'lucide-react';
import Reveal from './Reveal';

const STEPS = [
  {
    icon: Upload,
    num: '01',
    title: 'Upload Your Files',
    body: 'Drop your resume (PDF or DOCX) and paste the job description. Both are parsed instantly — no formatting lost.',
    color: '#ff2e2e',
  },
  {
    icon: ScanSearch,
    num: '02',
    title: 'See the Gap',
    body: 'Get a honest ATS match score with five sub-scores. The system tells you exactly which skills and keywords are missing.',
    color: '#e02626',
  },
  {
    icon: FileOutput,
    num: '03',
    title: 'Review & Download',
    body: 'Every proposed change appears in a review panel. Accept all or pick individual patches, then download your tailored resume as DOCX or PDF.',
    color: '#10b981',
  },
];

export default function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="section-anchor py-20 md:py-28 relative"
      style={{ background: '#ffffff' }}
    >
      {/* Top red wedge that bleeds in from the dark section above */}
      <div
        aria-hidden
        className="absolute top-0 left-0 right-0 h-24 -translate-y-full"
        style={{
          background: 'linear-gradient(180deg, #000 0%, transparent 100%)',
        }}
      />

      <div className="max-w-5xl mx-auto px-6">
        <Reveal className="text-center mb-14">
          <p
            className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest mb-4"
            style={{ color: '#ff2e2e' }}
          >
            <span style={{ color: '#ff2e2e' }}>●</span> How It Works
          </p>
          <h2
            className="font-display text-4xl md:text-5xl mb-4"
            style={{ color: '#0a0a0a' }}
          >
            Three steps to a{' '}
            <span style={{ color: '#ff2e2e' }}>tailored resume</span>
          </h2>
        </Reveal>

        <div className="relative grid md:grid-cols-3 gap-6">
          {/* Connector lines between cards */}
          <div
            className="hidden md:block absolute top-16 left-1/3 right-1/3 h-px"
            style={{
              background:
                'linear-gradient(90deg, #ff2e2e, #e02626, #10b981)',
              opacity: 0.4,
            }}
          />

          {STEPS.map((step, i) => {
            const Icon = step.icon;
            return (
              <Reveal key={step.num} delay={i * 0.12}>
                <div
                  className="relative p-7 rounded-3xl text-center transition-transform duration-300 hover:-translate-y-1"
                  style={{
                    background: '#ffffff',
                    border: '1px solid #e8e8e8',
                    boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
                  }}
                >
                  {/* Step number */}
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span
                      className="inline-block px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold"
                      style={{
                        background: step.color,
                        color: '#fff',
                        boxShadow: `0 0 16px ${step.color}60`,
                      }}
                    >
                      {step.num}
                    </span>
                  </div>

                  <div
                    className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
                    style={{
                      background: `linear-gradient(135deg, ${step.color}18, ${step.color}08)`,
                      border: `1px solid ${step.color}30`,
                    }}
                  >
                    <Icon size={26} style={{ color: step.color }} />
                  </div>

                  <h3 className="text-lg font-bold mb-2" style={{ color: '#0a0a0a' }}>{step.title}</h3>
                  <p className="text-sm leading-relaxed" style={{ color: '#555' }}>
                    {step.body}
                  </p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
