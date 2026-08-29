import Link from 'next/link';
import { Github, Heart } from 'lucide-react';

export default function Footer() {
  return (
    <footer
      style={{ borderTop: '1px solid rgba(255,46,46,0.10)' }}
    >
      <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>
            ResumeAI · Built with FastAPI + Next.js
          </span>
        </div>

        <div className="flex items-center gap-6">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-medium transition-colors duration-200"
            style={{ color: 'var(--text-muted)' }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--text-muted)')}
          >
            <Github size={13} />
            GitHub
          </a>

          <Link
            href="/tool"
            className="text-xs font-medium transition-colors duration-200"
            style={{ color: 'var(--text-muted)' }}
            onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--text-secondary)')}
            onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--text-muted)')}
          >
            Open Tool
          </Link>
        </div>
      </div>
    </footer>
  );
}
