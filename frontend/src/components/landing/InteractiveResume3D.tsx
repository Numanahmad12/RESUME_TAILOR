import React, { useRef, useEffect, useState, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/dist/ScrollTrigger';
import { Sparkles, Trophy, CheckCircle2, Award, Zap, FileText, Cpu, ShieldCheck } from 'lucide-react';

if (typeof window !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);
}

export default function InteractiveResume3D() {
  const groupRef = useRef<THREE.Group>(null);
  const cardGroupRef = useRef<THREE.Group>(null);
  const badgesGroupRef = useRef<THREE.Group>(null);
  const particlesRef = useRef<THREE.Points>(null);
  
  const mouse = useRef({ x: 0, y: 0, targetX: 0, targetY: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const { size } = useThree();
  const isMobile = size.width < 768;

  // Track mouse coordinates normalized between -1 and 1
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const { innerWidth, innerHeight } = window;
      mouse.current.targetX = (e.clientX / innerWidth) * 2 - 1;
      mouse.current.targetY = -(e.clientY / innerHeight) * 2 + 1;
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // GSAP ScrollTrigger: Drive 3D transformations as user scrolls down the page
  useEffect(() => {
    if (typeof window === 'undefined' || !groupRef.current) return;

    const ctx = gsap.context(() => {
      // Scroll animation: tilt, elevate, and expand badges as the visitor scrolls
      gsap.to(groupRef.current!.rotation, {
        x: 0.35,
        y: -0.45,
        z: 0.08,
        ease: 'power1.out',
        scrollTrigger: {
          trigger: '#hero-section',
          start: 'top top',
          end: 'bottom top',
          scrub: 1.2,
        },
      });

      gsap.to(groupRef.current!.position, {
        y: -0.4,
        z: -0.8,
        ease: 'power1.out',
        scrollTrigger: {
          trigger: '#hero-section',
          start: 'top top',
          end: 'bottom top',
          scrub: 1.2,
        },
      });

      if (badgesGroupRef.current) {
        gsap.to(badgesGroupRef.current.position, {
          z: 0.6,
          y: 0.2,
          ease: 'power1.out',
          scrollTrigger: {
            trigger: '#hero-section',
            start: 'top top',
            end: 'bottom top',
            scrub: 1.5,
          },
        });
      }
    });

    return () => ctx.revert();
  }, []);

  // Ambient 3D floating particles
  const particleCount = isMobile ? 50 : 140;
  const particlePositions = useMemo(() => {
    const arr = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      const r = 3.5 + Math.random() * 2.5;
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, [particleCount]);

  // Frame loop: lerp mouse rotation and gentle floating levitation
  useFrame((state, delta) => {
    // Smooth lerp mouse coordinates
    mouse.current.x += (mouse.current.targetX - mouse.current.x) * 0.06;
    mouse.current.y += (mouse.current.targetY - mouse.current.y) * 0.06;

    if (cardGroupRef.current) {
      // Gentle floating levitation
      const floatY = Math.sin(state.clock.elapsedTime * 1.6) * 0.08;
      const floatRotZ = Math.sin(state.clock.elapsedTime * 0.8) * 0.02;

      // Mouse interactive tilt (pitch & yaw)
      const targetRotY = mouse.current.x * 0.35;
      const targetRotX = -mouse.current.y * 0.25;

      cardGroupRef.current.position.y = floatY;
      cardGroupRef.current.rotation.z = floatRotZ;
      cardGroupRef.current.rotation.y += (targetRotY - cardGroupRef.current.rotation.y) * 0.08;
      cardGroupRef.current.rotation.x += (targetRotX - cardGroupRef.current.rotation.x) * 0.08;
    }

    if (particlesRef.current) {
      particlesRef.current.rotation.y += delta * 0.03;
      particlesRef.current.rotation.x += delta * 0.015;
    }
  });

  return (
    <group ref={groupRef}>
      {/* ── Background Floating Ambient Particle Cloud ─────────────────── */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particleCount}
            array={particlePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#ff3366"
          size={0.045}
          sizeAttenuation
          transparent
          opacity={0.65}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>

      {/* ── Main 3D Resume Slab & HTML Content ─────────────────────────── */}
      <group
        ref={cardGroupRef}
        onPointerEnter={() => setIsHovered(true)}
        onPointerLeave={() => setIsHovered(false)}
      >
        {/* Physical 3D Backplate & Bevel Edge */}
        <mesh position={[0, 0, -0.04]}>
          <boxGeometry args={[3.2, 4.4, 0.06]} />
          <meshPhysicalMaterial
            color="#080812"
            metalness={0.85}
            roughness={0.2}
            clearcoat={0.6}
            clearcoatRoughness={0.15}
            transmission={0.3}
            transparent
            opacity={0.92}
          />
        </mesh>

        {/* Outer glowing border ring */}
        <mesh position={[0, 0, -0.05]}>
          <boxGeometry args={[3.26, 4.46, 0.02]} />
          <meshBasicMaterial
            color="#ff2e55"
            transparent
            opacity={isHovered ? 0.65 : 0.35}
          />
        </mesh>

        {/* Crisp, Ultra-Realistic 3D Formatted Resume Document */}
        <Html
          transform
          distanceFactor={3.6}
          position={[0, 0, 0.02]}
          className="pointer-events-none select-none"
        >
          <div className="w-[380px] h-[520px] rounded-2xl bg-gradient-to-b from-[#0c0c17]/95 via-[#0e0e1b]/95 to-[#080810]/98 border border-red-500/30 shadow-[0_0_50px_rgba(255,46,70,0.25)] p-5 text-slate-200 overflow-hidden relative backdrop-blur-xl font-sans text-xs">
            {/* Holographic Specular Light Sweep */}
            <div
              className="absolute inset-0 pointer-events-none opacity-40 mix-blend-overlay transition-opacity duration-300"
              style={{
                background:
                  'radial-gradient(circle at 60% 30%, rgba(255,255,255,0.4) 0%, rgba(255,80,120,0.15) 35%, transparent 70%)',
              }}
            />

            {/* Glowing Laser Scanner Beam moving across the document */}
            <div
              className="absolute left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-red-500 to-transparent pointer-events-none animate-scan-laser shadow-[0_0_12px_#ff2e55]"
              style={{
                animation: 'resumeLaserScan 4.2s ease-in-out infinite',
              }}
            />

            {/* Header: Candidate & Contact */}
            <div className="border-b border-slate-800 pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-black tracking-tight text-white uppercase font-mono">
                      ALEX MORGAN
                    </h3>
                    <span className="flex h-2 w-2 relative">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                    </span>
                  </div>
                  <p className="text-[11px] font-semibold text-red-400 tracking-wide mt-0.5">
                    Lead AI/ML Systems Engineer
                  </p>
                </div>
                {/* Live ATS Ribbon */}
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/40 text-red-300 shadow-[0_0_15px_rgba(255,46,70,0.3)]">
                  <Zap size={11} className="text-red-400 fill-red-400 animate-pulse" />
                  <span className="font-mono text-[10px] font-black tracking-wider">98% MATCH</span>
                </div>
              </div>

              <div className="flex items-center gap-3 text-[10px] text-slate-400 mt-2 font-mono">
                <span>📍 San Francisco, CA</span>
                <span>✉️ alex.ai@engineer.io</span>
                <span>🔗 github.com/alex-ai</span>
              </div>
            </div>

            {/* Summary Section */}
            <div className="pt-2.5 pb-2">
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Executive Profile
              </span>
              <p className="text-[10.5px] leading-relaxed text-slate-300">
                High-impact engineer specializing in end-to-end LLM architectures, RAG pipelines, and high-concurrency model inference. Proven record reducing inference latency by 45% while maintaining 99.8% precision.
              </p>
            </div>

            {/* Technical Skills Badges */}
            <div className="py-2 border-t border-slate-800/80">
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                Target ATS Skills Verified
              </span>
              <div className="flex flex-wrap gap-1.5">
                {['Python', 'PyTorch', 'LangChain', 'FastAPI', 'PostgreSQL', 'Docker', 'RAG'].map((skill) => (
                  <span
                    key={skill}
                    className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700/80 text-[9.5px] text-slate-200 font-mono font-medium shadow-sm flex items-center gap-1"
                  >
                    <CheckCircle2 size={9} className="text-emerald-400" />
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Experience Bullets */}
            <div className="py-2 border-t border-slate-800/80">
              <div className="flex justify-between items-baseline mb-1">
                <span className="text-[11px] font-bold text-slate-100">Senior ML Engineer · ScaleTech AI</span>
                <span className="text-[9.5px] font-mono text-slate-400">2023 – Present</span>
              </div>
              <ul className="space-y-1 text-[10px] text-slate-300 list-disc list-inside leading-snug">
                <li>
                  Architected RAG system indexing 5M+ technical documents with sub-60ms retrieval.
                </li>
                <li>
                  Engineered automated evaluation pipeline boosting model accuracy from 82% to 96.4%.
                </li>
              </ul>
            </div>

            {/* Achievements & Certifications Split */}
            <div className="pt-2 border-t border-slate-800/80 flex gap-2">
              <div className="flex-1 bg-slate-950/60 p-1.5 rounded-lg border border-slate-800">
                <div className="flex items-center gap-1 text-[9px] font-bold text-amber-300 uppercase">
                  <Trophy size={10} className="text-amber-400" />
                  Achievements
                </div>
                <p className="text-[9.5px] text-slate-300 truncate mt-0.5">AIR 21 · National Finalist</p>
              </div>

              <div className="flex-1 bg-slate-950/60 p-1.5 rounded-lg border border-slate-800">
                <div className="flex items-center gap-1 text-[9px] font-bold text-indigo-300 uppercase">
                  <Award size={10} className="text-indigo-400" />
                  Certifications
                </div>
                <p className="text-[9.5px] text-slate-300 truncate mt-0.5">DeepLearning.AI / Coursera</p>
              </div>
            </div>

            {/* Bottom Status Bar */}
            <div className="absolute bottom-2 left-5 right-5 flex justify-between items-center text-[9px] text-slate-500 font-mono pt-1 border-t border-slate-800/50">
              <span className="flex items-center gap-1 text-emerald-400">
                <ShieldCheck size={10} /> Grounded Fact-Check: 100%
              </span>
              <span>Jake's Format · Single Page</span>
            </div>
          </div>
        </Html>
      </group>

      {/* ── Floating 3D Metric Badges in Parallax Space ────────────────── */}
      <group ref={badgesGroupRef}>
        {/* Floating Badge 1: Top-Right ATS Score Orb */}
        <Html
          transform
          distanceFactor={3.6}
          position={[1.7, 1.4, 0.4]}
          className="pointer-events-none select-none"
        >
          <div className="px-3 py-2 rounded-xl bg-slate-950/90 border border-emerald-500/50 shadow-[0_0_30px_rgba(16,185,129,0.35)] backdrop-blur-md flex items-center gap-2.5 text-white">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold font-mono text-xs">
              98%
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 leading-tight">
                ATS Optimized
              </p>
              <p className="text-[9px] text-slate-400 leading-tight">Ready for Top 1% Roles</p>
            </div>
          </div>
        </Html>

        {/* Floating Badge 2: Bottom-Left Real Achievement */}
        <Html
          transform
          distanceFactor={3.6}
          position={[-1.6, -1.5, 0.35]}
          className="pointer-events-none select-none"
        >
          <div className="px-3 py-2 rounded-xl bg-slate-950/90 border border-amber-500/50 shadow-[0_0_30px_rgba(245,158,11,0.3)] backdrop-blur-md flex items-center gap-2 text-white">
            <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
              <Trophy size={14} />
            </div>
            <div>
              <p className="text-[10px] font-bold text-amber-300 leading-tight">National Finalist</p>
              <p className="text-[9px] text-slate-400 leading-tight">Robocon · AIR 21</p>
            </div>
          </div>
        </Html>

        {/* Floating Badge 3: Mid-Right Zero Hallucinations */}
        <Html
          transform
          distanceFactor={3.6}
          position={[1.5, -0.6, 0.25]}
          className="pointer-events-none select-none"
        >
          <div className="px-2.5 py-1.5 rounded-lg bg-slate-950/90 border border-indigo-500/40 shadow-[0_0_20px_rgba(99,102,241,0.25)] backdrop-blur-md flex items-center gap-1.5 text-[9.5px] text-slate-200">
            <Cpu size={12} className="text-indigo-400" />
            <span className="font-semibold text-slate-300">Grounded RAG Pipeline</span>
          </div>
        </Html>
      </group>

      {/* Global Style for Keyframe Laser Scan */}
      <Html>
        <style>{`
          @keyframes resumeLaserScan {
            0% { top: 0%; opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
          }
        `}</style>
      </Html>
    </group>
  );
}
