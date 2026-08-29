/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // ─── Red accent ramp (replaces brand indigo) ───
        brand: {
          50:  '#fff1f1',
          100: '#ffdfdf',
          200: '#ffc0c0',
          300: '#ff9a9a',
          400: '#ff7a7a',
          500: '#ff2e2e',
          600: '#e02626',
          700: '#b81e1e',
          800: '#8a1616',
          900: '#5c0f0f',
          950: '#2e0808',
        },
        // Cherry-blossom pink secondary
        accent: {
          400: '#ff7a9a',
          500: '#ff5c8a',
          600: '#e0407a',
        },
        sky: {
          400: '#ff7a7a',
        },
        // Hard B/W surface tokens
        surface: {
          1: '#000000',
          2: '#0a0a0a',
          3: '#111111',
          4: '#1a1a1a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial':   'radial-gradient(var(--tw-gradient-stops))',
        'gradient-brand':    'linear-gradient(135deg, #ff2e2e 0%, #e02626 100%)',
        'gradient-brand-2':  'linear-gradient(135deg, #ff5c8a 0%, #ff7a9a 100%)',
        'gradient-success':  'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        'gradient-light':    'linear-gradient(180deg, #ffffff 0%, #f5f5f5 100%)',
      },
      boxShadow: {
        'glow-sm':    '0 0 16px rgba(255,46,46,0.3)',
        'glow':       '0 0 32px rgba(255,46,46,0.4)',
        'glow-lg':    '0 0 60px rgba(255,46,46,0.45)',
        'glow-xl':    '0 0 100px rgba(255,46,46,0.5)',
        'glass':      '0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.05)',
        'glass-lg':   '0 24px 60px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.06)',
        'success':    '0 0 24px rgba(16,185,129,0.35)',
      },
      borderColor: {
        glass:       'rgba(255,255,255,0.08)',
        'glass-2':   'rgba(255,255,255,0.15)',
        'glass-3':   'rgba(255,46,46,0.5)',
      },
      backdropBlur: {
        glass: '20px',
      },
      animation: {
        'fade-in':    'fadeIn 0.4s ease-out both',
        'slide-up':   'slideUp 0.5s ease-out both',
        'scale-in':   'scaleIn 0.35s ease-out both',
        'spin-slow':  'spin 2s linear infinite',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4,0,0.6,1) infinite',
        'float':      'float-badge 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          from: { opacity: '0', transform: 'scale(0.94)' },
          to:   { opacity: '1', transform: 'scale(1)' },
        },
        'float-badge': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':       { transform: 'translateY(-4px)' },
        },
      },
      transitionDuration: {
        250: '250ms',
      },
    },
  },
  plugins: [],
};
