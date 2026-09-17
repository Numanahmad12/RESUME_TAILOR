import { useEffect, useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Environment } from '@react-three/drei';
import InteractiveResume3D from './InteractiveResume3D';
import { Trophy, Zap, ShieldCheck } from 'lucide-react';

/**
 * HeroScene — wraps the 3D interactive Resume scene. Lazy-loaded by Hero.tsx (ssr: false).
 */
export default function HeroScene() {
  const [prefersDesktop3D, setPrefersDesktop3D] = useState<boolean | null>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mqMobile = window.matchMedia('(max-width: 768px)');
    const mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');

    const update = () => {
      setPrefersDesktop3D(!mqMobile.matches && !mqReduce.matches);
    };
    update();

    mqMobile.addEventListener('change', update);
    mqReduce.addEventListener('change', update);
    return () => {
      mqMobile.removeEventListener('change', update);
      mqReduce.removeEventListener('change', update);
    };
  }, []);

  // First render before media query resolves → show static fallback
  if (prefersDesktop3D === null || !prefersDesktop3D) {
    return <StaticFallback />;
  }

  return (
    <Canvas
      dpr={[1, 2]}
      camera={{ position: [0, 0, 7.2], fov: 46 }}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      style={{ width: '100%', height: '100%' }}
    >
      <ambientLight intensity={0.7} />
      <directionalLight position={[4, 5, 6]} intensity={1.2} color="#ffffff" />
      <directionalLight position={[-4, -2, -3]} intensity={0.5} color="#ff3366" />
      <pointLight position={[0, 2, 3]} intensity={0.8} color="#ff7a9a" />
      <Suspense fallback={null}>
        <InteractiveResume3D />
        <Environment preset="city" />
      </Suspense>
    </Canvas>
  );
}

/** Rich CSS 3D fallback for mobile / reduced-motion. */
function StaticFallback() {
  return (
    <div className="w-full h-full relative flex items-center justify-center p-4">
      {/* Background radial glow */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            'radial-gradient(circle at 50% 50%, rgba(255,46,70,0.25) 0%, transparent 65%)',
        }}
      />
      
      {/* CSS 3D Tilted Resume Card */}
      <div
        className="relative w-full max-w-[340px] rounded-2xl bg-slate-950/90 border border-red-500/40 p-5 shadow-[0_0_50px_rgba(255,46,70,0.25)] backdrop-blur-xl text-left text-xs transition-transform duration-500 hover:rotate-0"
        style={{
          transform: 'perspective(1000px) rotateY(-8deg) rotateX(6deg)',
        }}
      >
        <div className="flex justify-between items-start border-b border-slate-800 pb-2.5">
          <div>
            <h4 className="font-bold text-white font-mono uppercase tracking-wide">ALEX MORGAN</h4>
            <p className="text-[11px] text-red-400 font-medium">Lead AI Systems Engineer</p>
          </div>
          <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 font-mono text-[10px] font-bold border border-red-500/40">
            <Zap size={10} className="text-red-400" /> 98% MATCH
          </span>
        </div>

        <div className="pt-2 text-[10px] text-slate-300 space-y-2">
          <p className="line-clamp-2 text-slate-400">
            High-impact engineer specializing in LLM architectures, RAG pipelines, and model latency reduction.
          </p>
          <div className="flex flex-wrap gap-1">
            {['Python', 'PyTorch', 'LangChain', 'Docker', 'FastAPI'].map((t) => (
              <span key={t} className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-[9px] font-mono text-slate-300">
                {t}
              </span>
            ))}
          </div>
        </div>

        <div className="mt-3 pt-2 border-t border-slate-800 flex justify-between items-center text-[9px] text-slate-400 font-mono">
          <span className="flex items-center gap-1 text-amber-400">
            <Trophy size={10} /> AIR 21 Finalist
          </span>
          <span className="flex items-center gap-1 text-emerald-400">
            <ShieldCheck size={10} /> 100% Grounded
          </span>
        </div>
      </div>
    </div>
  );
}
