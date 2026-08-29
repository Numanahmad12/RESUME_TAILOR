import { motion, useReducedMotion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

type FeatureCardProps = {
  icon: LucideIcon;
  title: string;
  body: string;
  accent: string; // hex color for the icon glow
  badge?: string; // small label, e.g. "Real-time"
  delay?: number;
};

export default function FeatureCard({
  icon: Icon,
  title,
  body,
  accent,
  badge,
  delay = 0,
}: FeatureCardProps) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-10% 0px' }}
      transition={{ delay, duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
      whileHover={
        reduce
          ? undefined
          : {
              rotateX: 4,
              rotateY: -4,
              transition: { duration: 0.25 },
            }
      }
      style={{ transformPerspective: 1000, transformStyle: 'preserve-3d' }}
      className="group relative p-6 rounded-2xl overflow-hidden h-full"
    >
      {/* Background */}
      <div
        className="absolute inset-0"
        style={{
          background: 'rgba(15,15,30,0.7)',
          border: '1px solid rgba(255,46,46,0.15)',
          boxShadow: '0 8px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)',
          backdropFilter: 'blur(12px)',
          WebkitBackdropFilter: 'blur(12px)',
        }}
      />
      {/* Glow on hover */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{
          background: `radial-gradient(circle at 50% 0%, ${accent}25 0%, transparent 60%)`,
        }}
      />
      {/* Border glow on hover */}
      <div
        className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{ boxShadow: `0 0 40px ${accent}40, inset 0 1px 0 ${accent}30` }}
      />

      <div className="relative" style={{ transform: 'translateZ(20px)' }}>
        <div className="flex items-start justify-between mb-4">
          <div
            className="w-11 h-11 rounded-xl flex items-center justify-center"
            style={{
              background: `linear-gradient(135deg, ${accent}30, ${accent}10)`,
              border: `1px solid ${accent}45`,
              boxShadow: `0 0 20px ${accent}25`,
            }}
          >
            <Icon size={20} style={{ color: accent }} />
          </div>
          {badge && (
            <span
              className="text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-md"
              style={{
                background: `${accent}12`,
                color: accent,
                border: `1px solid ${accent}30`,
              }}
            >
              {badge}
            </span>
          )}
        </div>
        <h3 className="text-base font-bold mb-2 text-white">{title}</h3>
        <p
          className="text-sm leading-relaxed"
          style={{ color: 'var(--text-secondary)' }}
        >
          {body}
        </p>
      </div>
    </motion.div>
  );
}
