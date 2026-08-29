import Nav from './Nav';
import Hero from './Hero';
import StatsBand from './StatsBand';
import FeatureGrid from './FeatureGrid';
import ScoringBreakdown from './ScoringBreakdown';
import PipelineSection from './PipelineSection';
import HowItWorks from './HowItWorks';
import CTASection from './CTASection';
import Footer from './Footer';

/**
 * LandingPage — composes the marketing page in render order.
 * Loaded by index.tsx via `dynamic({ ssr: false })`, so it can safely
 * use browser-only APIs (matchMedia, scroll, canvas).
 */
export default function LandingPage() {
  return (
    <div className="min-h-screen relative">
      {/* Animated background (kept from original site) */}
      <div className="bg-canvas">
        <div className="bg-grid" />
        <div className="bg-orb bg-orb-1" />
        <div className="bg-orb bg-orb-2" />
        <div className="bg-orb bg-orb-3" />
      </div>

      <div className="relative z-10">
        <Nav />
        <main>
          <Hero />
          <StatsBand />
          <FeatureGrid />
          <ScoringBreakdown />
          <PipelineSection />
          <HowItWorks />
          <CTASection />
        </main>
        <Footer />
      </div>
    </div>
  );
}
