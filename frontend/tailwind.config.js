/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
          600: '#475569',
          500: '#64748b',
          400: '#94a3b8',
          300: '#cbd5e1',
          200: '#e2e8f0',
          100: '#f1f5f9',
          50: '#f8fafc',
        },
        teal: {
          500: '#14b8a6',
        },
        cyan: {
          500: '#06b6d4',
        },
        sky: {
          500: '#0ea5e9',
        },
        indigo: {
          500: '#6366f1',
        }
      },
      spacing: {
        '2': '8px',
        '4': '16px',
        '6': '24px',
        '8': '32px',
        '12': '48px',
      },
      fontSize: {
        'caption': ['14px', '1.4'],
        'body': ['18px', '1.5'],
        'heading': ['32px', '1.2'],
        'display': ['48px', '1.1'],
      },
      keyframes: {
        ripple: {
          '0%': { width: '0px', height: '0px', opacity: '0.4' },
          '100%': { width: '500px', height: '500px', opacity: '0' },
        }
      },
      animation: {
        ripple: 'ripple 600ms ease-out forwards',
      }
    },
  },
  plugins: [],
}