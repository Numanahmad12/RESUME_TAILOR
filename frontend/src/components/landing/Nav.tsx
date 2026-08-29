import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Github, Menu } from 'lucide-react';
import { useState } from 'react';

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <motion.nav
      initial={false}
      animate={{
        background: scrolled
          ? 'rgba(0,0,0,0.85)'
          : 'rgba(0,0,0,0)',
        borderBottom: scrolled
          ? '1px solid rgba(255,46,46,0.15)'
          : '1px solid transparent',
        backdropFilter: scrolled ? 'blur(24px) saturate(180%)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(24px) saturate(180%)' : 'none',
      }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className="sticky top-0 z-50 w-full px-6 py-3"
    >
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg,#ff2e2e,#ff5c8a)',
              boxShadow: '0 0 20px rgba(255,46,46,0.5)',
            }}
          >
            <ArrowRight size={16} className="text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight text-white">
            Resume<span style={{ color: '#ff2e2e' }}>AI</span>
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {['How it works', 'Features', 'Pricing'].map((item) => (
            <a
              key={item}
              href="#"
              className="text-sm font-medium transition-colors duration-200"
              style={{ color: 'rgba(255,255,255,0.6)' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#fff')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.6)')}
            >
              {item}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/tool"
            className="hidden sm:inline-flex items-center gap-2 px-5 py-2 rounded-full text-sm font-semibold text-white cursor-pointer transition-all duration-200"
            style={{
              background: '#ff2e2e',
              boxShadow: '0 4px 20px rgba(255,46,46,0.4)',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.transform = 'translateY(-1px)';
              (e.currentTarget as HTMLElement).style.boxShadow = '0 8px 30px rgba(255,46,46,0.6)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.transform = 'translateY(0)';
              (e.currentTarget as HTMLElement).style.boxShadow = '0 4px 20px rgba(255,46,46,0.4)';
            }}
          >
            Launch Tool
            <ArrowRight size={14} />
          </Link>
          <button
            className="md:hidden w-10 h-10 rounded-lg flex items-center justify-center"
            style={{ background: 'rgba(255,255,255,0.05)', color: '#fff' }}
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            <Menu size={20} />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          className="md:hidden mt-3 p-4 rounded-xl"
          style={{
            background: 'rgba(0,0,0,0.9)',
            border: '1px solid rgba(255,46,46,0.2)',
            backdropFilter: 'blur(20px)',
          }}
        >
          <div className="flex flex-col gap-2">
            {['How it works', 'Features', 'Pricing'].map((item) => (
              <a
                key={item}
                href="#"
                className="px-3 py-2 rounded-lg text-sm"
                style={{ color: 'rgba(255,255,255,0.7)' }}
              >
                {item}
              </a>
            ))}
            <Link
              href="/tool"
              className="px-3 py-2 rounded-lg text-sm font-semibold text-center"
              style={{ background: '#ff2e2e', color: '#fff' }}
            >
              Launch Tool
            </Link>
          </div>
        </div>
      )}
    </motion.nav>
  );
}