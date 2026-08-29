import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/dist/ScrollTrigger';
import {
  FileText,
  ScanSearch,
  GitCompare,
  Wand2,
  ShieldCheck,
  Eye,
  FileOutput,
  Download,
} from 'lucide-react';
import PipelineCard from './PipelineCard';
import Reveal from './Reveal';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

const STAGES = [
  { icon: FileText,    title: 'Ingestion',         body: 'PDF and DOCX parsing with structure recovery — tables, bullet lists, and section headers all map to a strict schema.', color: '#ff2e2e' },
  { icon: ScanSearch,  title: 'JD Analysis',       body: 'Required vs. preferred skills, years of experience, and responsibilities are extracted with calibrated NLP rules.', color: '#ff5c8a' },
  { icon: GitCompare,  title: 'Gap Analysis',      body: 'Five sub-scores measure keyword coverage, experience fit, responsibility alignment, impact, and formatting.', color: '#ff7a9a' },
  { icon: Wand2,       title: 'Generation',        body: 'Heuristic patch generator rewrites the summary, reorders skills, and upgrades weak bullets to quantified ones.', color: '#e02626' },
  { icon: ShieldCheck, title: 'Validation',        body: 'Every patch is checked against the original resume — no fabricated skills, no broken bullets, no scope drift.', color: '#10b981' },
  { icon: Eye,         title: 'Review',            body: 'You see every change side-by-side. Accept, edit, or reject before anything is committed to the final document.', color: '#f59e0b' },
  { icon: FileOutput,  title: 'Rendering',         body: 'DOCX and PDF renderers produce a clean, ATS-safe output that preserves your bullet density and contact info.', color: '#ff2e2e' },
  { icon: Download,    title: 'Export',            body: 'Download the tailored resume. Re-upload it later and watch the ATS score increase on each round.', color: '#ff5c8a' },
];

/**
 * PipelineSection — horizontally-pinned scroll experience.
 *
 *  • On desktop: 8 cards pin in place and translate horizontally as the user scrolls.
 *  • On mobile (<768px) / reduced motion: falls back to a vertical list with reveal animations.
 */
export default function PipelineSection() {
  const sectionRef = useRef<HTMLElement>(null);
  const trackRef = useRef<HTMLDivElement>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isMobile, setIsMobile] = useState<boolean | null>(null);
  const [prefersReduce, setPrefersReduce] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mq = window.matchMedia('(max-width: 768px)');
    const mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => {
      setIsMobile(mq.matches);
      setPrefersReduce(mqReduce.matches);
    };
    update();
    mq.addEventListener('change', update);
    mqReduce.addEventListener('change', update);
    return () => {
      mq.removeEventListener('change', update);
      mqReduce.removeEventListener('change', update);
    };
  }, []);

  useEffect(() => {
    if (isMobile === null) return;
    if (isMobile || prefersReduce) return; // skip pin on mobile / reduced

    const section = sectionRef.current;
    const track = trackRef.current;
    if (!section || !track) return;

    const ctx = gsap.context(() => {
      // Calculate how far we need to translate: (total width) - (viewport width)
      const getDistance = () => track.scrollWidth - window.innerWidth + 80;

      gsap.to(track, {
        x: () => -getDistance(),
        ease: 'none',
        scrollTrigger: {
          trigger: section,
          start: 'top top',
          end: () => `+=${getDistance()}`,
          pin: true,
          scrub: 1,
          anticipatePin: 1,
          invalidateOnRefresh: true,
          onUpdate: (self) => {
            const idx = Math.min(
              STAGES.length - 1,
              Math.floor(self.progress * STAGES.length * 0.999)
            );
            setActiveIndex(idx);
          },
        },
      });
    }, section);

    return () => ctx.revert();
  }, [isMobile, prefersReduce]);

  // Fallback (mobile / reduced): active card follows scroll position via IntersectionObserver
  useEffect(() => {
    if (isMobile === null) return;
    if (!isMobile && !prefersReduce) return;

    const cards = sectionRef.current?.querySelectorAll('[data-stage-card]');
    if (!cards) return;

    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const idx = Number((e.target as HTMLElement).dataset.stageCard);
            if (!Number.isNaN(idx)) setActiveIndex(idx);
          }
        });
      },
      { rootMargin: '-40% 0px -40% 0px', threshold: 0 }
    );
    cards.forEach((c) => obs.observe(c));
    return () => obs.disconnect();
  }, [isMobile, prefersReduce]);

  return (
    <section
      id="pipeline"
      ref={sectionRef}
      className="section-anchor relative py-20 md:py-28 overflow-hidden"
      style={{
        // mobile: no pin height
        minHeight: isMobile === false && !prefersReduce ? '100vh' : undefined,
      }}
    >
      <div className="max-w-6xl mx-auto px-6 mb-10">
        <Reveal className="text-center">
          <p
            className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-widest mb-4"
            style={{ color: '#ff7a7a' }}
          >
            <span style={{ color: '#ff2e2e' }}>●</span> Pipeline
          </p>
          <h2
            className="font-display text-4xl md:text-5xl mb-4"
            style={{ letterSpacing: '-0.04em' }}
          >
            From upload to download in{' '}
            <span style={{ color: '#ff2e2e' }}>eight stages</span>
          </h2>
          <p className="text-base max-w-2xl mx-auto" style={{ color: 'var(--text-secondary)' }}>
            Every stage is observable, deterministic, and grounded. Scroll to walk through
            the full pipeline.
          </p>
        </Reveal>
      </div>

      {/* Horizontal track (desktop) / vertical list (mobile) */}
      <div
        ref={trackRef}
        className={
          isMobile === false && !prefersReduce
            ? 'flex gap-6 pl-[max(2rem,calc((100vw-72rem)/2))]'
            : 'flex flex-col gap-4 max-w-3xl mx-auto px-6'
        }
        style={{ willChange: 'transform' }}
      >
        {STAGES.map((stage, i) => {
          const Icon = stage.icon;
          return (
            <div key={stage.title} data-stage-card={i} className={isMobile === false && !prefersReduce ? 'snap-start' : ''}>
              <PipelineCard
                index={i}
                total={STAGES.length}
                title={stage.title}
                body={stage.body}
                color={stage.color}
                active={activeIndex === i}
                icon={<Icon size={22} style={{ color: stage.color }} />}
              />
            </div>
          );
        })}
      </div>

      {/* Progress dots */}
      <div className="max-w-6xl mx-auto px-6 mt-8 flex items-center justify-center gap-2">
        {STAGES.map((_, i) => (
          <div
            key={i}
            className="h-1.5 rounded-full transition-all duration-300"
            style={{
              width: activeIndex === i ? 28 : 8,
              background:
                activeIndex === i
                  ? 'linear-gradient(90deg, #ff2e2e, #ff7a9a)'
                  : 'rgba(255,46,46,0.18)',
              boxShadow: activeIndex === i ? '0 0 10px rgba(255,46,46,0.45)' : 'none',
            }}
          />
        ))}
      </div>
    </section>
  );
}
