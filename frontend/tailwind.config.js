/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Primary Navy - RCM brand identity
        primary: {
          50:  '#EEF3FA',
          100: '#D5E3F4',
          200: '#ACC6E8',
          300: '#82A9DD',
          400: '#598DD1',
          500: '#2F70C5',
          600: '#1D5BA8',
          700: '#1E3A5F', // Deep Navy - main brand
          800: '#162B47',
          900: '#0D1D2F',
          950: '#070E17',
        },
        // Corporate Blue - active states, interactive
        blue: {
          50:  '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        // Forest Green - success, paid, collected
        forest: {
          50:  '#ECFDF5',
          100: '#D1FAE5',
          200: '#A7F3D0',
          300: '#6EE7B7',
          400: '#34D399',
          500: '#10B981',
          600: '#059669',
          700: '#047857',
          800: '#065F46',
          900: '#064E3B',
        },
        // Amber - warning, at-risk, pending
        amber: {
          50:  '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        // Crimson - denied, danger, overdue
        crimson: {
          50:  '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
        // Slate - backgrounds and surfaces
        slate: {
          25:  '#FAFBFC',
          50:  '#F8FAFC',
          100: '#F1F5F9',
          150: '#EEF2F7',
          200: '#E4E7EB',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
          950: '#020617',
        },
        // Sidebar navy tokens
        sidebar: {
          bg:         '#1E3A5F',
          'bg-hover':  '#162B47',
          'bg-active': '#2563EB',
          text:        '#CBD5E1',
          'text-active': '#FFFFFF',
          border:     '#243D5E',
          icon:       '#94A3B8',
          'icon-active': '#FFFFFF',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.625rem', { lineHeight: '1rem' }],
      },
      boxShadow: {
        'card':       '0 1px 3px 0 rgba(15,23,42,0.06), 0 1px 2px -1px rgba(15,23,42,0.04)',
        'card-hover': '0 4px 12px 0 rgba(15,23,42,0.10), 0 2px 4px -2px rgba(15,23,42,0.06)',
        'card-xl':    '0 8px 24px 0 rgba(15,23,42,0.12), 0 4px 8px -4px rgba(15,23,42,0.08)',
        'modal':      '0 20px 60px 0 rgba(15,23,42,0.20), 0 8px 16px -8px rgba(15,23,42,0.12)',
        'dropdown':   '0 8px 24px 0 rgba(15,23,42,0.12), 0 2px 4px 0 rgba(15,23,42,0.06)',
        'inset-sm':   'inset 0 1px 2px rgba(15,23,42,0.06)',
        'btn':        '0 1px 2px 0 rgba(15,23,42,0.08)',
        'btn-primary':'0 2px 4px 0 rgba(30,58,95,0.30)',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      animation: {
        'fade-in':      'fadeIn 150ms ease-out',
        'fade-out':     'fadeOut 100ms ease-in',
        'slide-up':     'slideUp 200ms cubic-bezier(0.16,1,0.3,1)',
        'slide-down':   'slideDown 200ms cubic-bezier(0.16,1,0.3,1)',
        'slide-right':  'slideRight 250ms cubic-bezier(0.16,1,0.3,1)',
        'shimmer':      'shimmer 1.5s infinite',
        'spin-slow':    'spin 2s linear infinite',
        'bounce-subtle':'bounceSm 1s ease-in-out infinite',
        'pulse-soft':   'pulseSoft 2s ease-in-out infinite',
        'count-up':     'countUp 400ms ease-out',
      },
      keyframes: {
        fadeIn: {
          from: { opacity: '0' },
          to:   { opacity: '1' },
        },
        fadeOut: {
          from: { opacity: '1' },
          to:   { opacity: '0' },
        },
        slideUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          from: { opacity: '0', transform: 'translateY(-8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          from: { opacity: '0', transform: 'translateX(-16px)' },
          to:   { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        bounceSm: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%':      { transform: 'translateY(-4px)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%':      { opacity: '0.6' },
        },
        countUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      transitionTimingFunction: {
        'spring': 'cubic-bezier(0.16,1,0.3,1)',
      },
      transitionDuration: {
        '150': '150ms',
        '250': '250ms',
        '350': '350ms',
      },
      backdropBlur: {
        xs: '2px',
      },
      screens: {
        'xs': '480px',
      },
    },
  },
  plugins: [],
}