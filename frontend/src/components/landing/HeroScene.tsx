import { useEffect, useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Environment, OrbitControls } from '@react-three/drei';
import DocumentBrain from './DocumentBrain';

/**
 * HeroScene — wraps the 3D scene. Lazy-loaded by Hero.tsx (ssr: false).
 *
 * On touch / small / reduced-motion devices the canvas is hidden and a
 * static CSS gradient fallback is rendered. The /tool route never imports
 * this file (it's only mounted by Hero.tsx on /).
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
      camera={{ position: [0, 0, 6.5], fov: 50 }}
      gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
      style={{ width: '100%', height: '100%' }}
    >
      <ambientLight intensity={0.5} />
      <directionalLight position={[3, 4, 5]} intensity={0.8} color="#ff7a9a" />
      <directionalLight position={[-4, -2, -3]} intensity={0.4} color="#ff5c8a" />
      <Suspense fallback={null}>
        <DocumentBrain />
        <Environment preset="night" />
      </Suspense>
      <OrbitControls
        enableZoom={false}
        enablePan={false}
        autoRotate
        autoRotateSpeed={0.4}
        makeDefault
      />
    </Canvas>
  );
}

/** Static, accessible fallback for mobile / reduced-motion / SSR-pre-mount. */
function StaticFallback() {
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
          className="w-20 h-28 rounded-md"
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
