import { motion, useReducedMotion, type MotionProps, type Variants } from 'framer-motion';
import { ReactNode } from 'react';

type RevealProps = {
  children: ReactNode;
  /** Vertical offset in px the element starts from. Default 24 */
  y?: number;
  /** Animation delay in seconds. Default 0 */
  delay?: number;
  /** Duration in seconds. Default 0.5 */
  duration?: number;
  /** Use scale instead of (or in addition to) y. Useful for icons. Default false */
  scale?: boolean;
  /** Once-only animation (good for landing-page sections). Default true */
  once?: boolean;
  /** Override the wrapper element. Default 'div' */
  as?: 'div' | 'section' | 'article' | 'header' | 'footer' | 'span' | 'li' | 'ul';
  /** Margin for the IntersectionObserver. Default '-10% 0px' (fires a bit before in-view) */
  margin?: string;
  className?: string;
} & Omit<MotionProps, 'variants' | 'initial' | 'whileInView' | 'viewport'>;

/**
 * Reveal — Framer Motion whileInView wrapper used by every landing section.
 * Respects prefers-reduced-motion automatically.
 */
export default function Reveal({
  children,
  y = 24,
  delay = 0,
  duration = 0.5,
  scale = false,
  once = true,
  as = 'div',
  margin = '-10% 0px',
  className,
  ...rest
}: RevealProps) {
  const reduce = useReducedMotion();

  const variants: Variants = {
    hidden: {
      opacity: 0,
      y: reduce ? 0 : y,
      scale: reduce ? 1 : scale ? 0.94 : 1,
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: reduce ? 0 : duration,
        delay: reduce ? 0 : delay,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  };

  const Tag = motion[as] as typeof motion.div;

  return (
    <Tag
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin }}
      variants={variants}
      className={className}
      {...rest}
    >
      {children}
    </Tag>
  );
}
