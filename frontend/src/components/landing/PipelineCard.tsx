import { motion, useReducedMotion } from 'framer-motion';
import { ReactNode } from 'react';

type PipelineCardProps = {
  index: number;
  total: number;
  title: string;
  body: string;
  icon: ReactNode;
  color: string;
  active: boolean;
};

export default function PipelineCard({
  index,
  total,
  title,
  body,
  icon,
  color,
  active,
}: PipelineCardProps) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      initial={{ opacity: 0.4, scale: 0.92, y: 12 }}
      animate={
        active
          ? { opacity: 1, scale: 1.04, y: 0 }
          : reduce
          ? { opacity: 0.65, scale: 0.95 }
          : { opacity: 0.55, scale: 0.94, y: 0 }
      }
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="flex-shrink-0 w-72 md:w-80 p-6 rounded-3xl relative"
      style={{
        background: 'rgba(15,15,30,0.75)',
        border: `1px solid ${active ? color + '60' : 'rgba(255,46,46,0.12)'}`,
        boxShadow: active
          ? `0 0 40px ${color}40, 0 12px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.06)`
          : '0 8px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
      }}
    >
      <div className="flex items-start justify-between mb-4">
        <div
          className="w-12 h-12 rounded-2xl flex items-center justify-center"
          style={{
            background: `linear-gradient(135deg, ${color}30, ${color}10)`,
            border: `1px solid ${color}50`,
            boxShadow: `0 0 18px ${color}30`,
          }}
        >
          {icon}
        </div>
        <span
          className="font-mono text-xs font-bold px-2.5 py-1 rounded-md"
          style={{
            color: active ? color : 'var(--text-muted)',
            background: active ? `${color}12` : 'rgba(255,255,255,0.04)',
            border: `1px solid ${active ? color + '40' : 'rgba(255,255,255,0.05)'}`,
          }}
        >
          {String(index + 1).padStart(2, '0')}/{String(total).padStart(2, '0')}
        </span>
      </div>
      <h3
        className="text-lg font-bold mb-2"
        style={{ color: active ? '#fff' : 'rgba(255,255,255,0.78)' }}
      >
        {title}
      </h3>
      <p
        className="text-sm leading-relaxed"
        style={{ color: active ? 'var(--text-secondary)' : 'var(--text-muted)' }}
      >
        {body}
      </p>
    </motion.div>
  );
}
