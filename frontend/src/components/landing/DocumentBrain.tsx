import { useRef, useMemo, useEffect, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

/**
 * DocumentBrain — the actual 3D content of the hero.
 *
 *   • A wireframe document plane (the resume) rotating slowly on Y.
 *   • A wireframe icosahedron "ATS brain" counter-rotating behind.
 *   • 200 additive-blended particles orbiting in a 6-radius sphere shell.
 *   • Document tilts toward the cursor via lerp.
 *   • Particle count drops to 60 on small viewports.
 */
export default function DocumentBrain() {
  const documentRef = useRef<THREE.Group>(null);
  const brainRef = useRef<THREE.Mesh>(null);
  const particlesRef = useRef<THREE.Points>(null);
  const mouse = useRef({ x: 0, y: 0 });

  const { size } = useThree();
  const isMobile = size.width < 768;
  const PARTICLE_COUNT = isMobile ? 60 : 200;

  // Track mouse position normalized to [-1, 1]
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mouse.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener('mousemove', onMove, { passive: true });
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  // Build a sphere-shell of particle positions (radius 6)
  const particlePositions = useMemo(() => {
    const arr = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      // Uniform sphere distribution
      const u = Math.random();
      const v = Math.random();
      const theta = 2 * Math.PI * u;
      const phi = Math.acos(2 * v - 1);
      const r = 5.5 + Math.random() * 1.5; // shell between 5.5 and 7
      arr[i * 3]     = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, [PARTICLE_COUNT]);

  useFrame((state, delta) => {
    // Document: rotate Y slowly, lerp toward mouse X
    if (documentRef.current) {
      documentRef.current.rotation.y += delta * 0.15;
      const targetY = mouse.current.x * 0.4;
      const targetX = mouse.current.y * 0.2;
      documentRef.current.rotation.y +=
        (targetY - documentRef.current.rotation.y) * 0.05;
      documentRef.current.rotation.x +=
        (targetX - documentRef.current.rotation.x) * 0.05;
    }

    // Brain: counter-rotate and slight bob
    if (brainRef.current) {
      brainRef.current.rotation.x += delta * 0.10;
      brainRef.current.rotation.y -= delta * 0.08;
      brainRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.15 - 0.3;
    }

    // Particles: slow rotation of the whole field
    if (particlesRef.current) {
      particlesRef.current.rotation.y += delta * 0.04;
      particlesRef.current.rotation.x += delta * 0.02;
    }
  });

  return (
    <group>
      {/* ── Resume document (wireframe plane) ─────────────────────── */}
      <group ref={documentRef} position={[0, 0, 0]}>
        <mesh>
          <planeGeometry args={[3.2, 4.2, 1, 1]} />
          <meshBasicMaterial
            color="#ff2e2e"
            wireframe
            transparent
            opacity={0.55}
          />
        </mesh>
        {/* Inner solid plane for depth */}
        <mesh position={[0, 0, -0.01]}>
          <planeGeometry args={[3.0, 4.0]} />
          <meshBasicMaterial color="#0d0d1a" transparent opacity={0.55} />
        </mesh>
        {/* "Lines of text" — three short horizontal bars */}
        {[1.4, 0.8, 0.2, -0.4, -1.0, -1.5].map((y, i) => (
          <mesh key={i} position={[(-0.6 + (i % 2) * 0.05), y, 0.01]}>
            <planeGeometry args={[1.6 - (i % 3) * 0.3, 0.06]} />
            <meshBasicMaterial color="#ff7a9a" transparent opacity={0.55} />
          </mesh>
        ))}
      </group>

      {/* ── ATS "brain" — counter-rotating icosahedron ────────────── */}
      <mesh ref={brainRef} position={[0, -0.3, -1.5]}>
        <icosahedronGeometry args={[1.2, 1]} />
        <meshBasicMaterial
          color="#ff7a9a"
          wireframe
          transparent
          opacity={0.45}
        />
      </mesh>

      {/* ── Particle field ───────────────────────────────────────── */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={PARTICLE_COUNT}
            array={particlePositions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#ff5c8a"
          size={0.05}
          sizeAttenuation
          transparent
          opacity={0.85}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </points>
    </group>
  );
}
