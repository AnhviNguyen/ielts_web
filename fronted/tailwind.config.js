/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        base: 'var(--bg-base)',
        surface: 'var(--bg-surface)',
        interactive: 'var(--bg-interactive)',
        accent: 'var(--spotify-green)',
        ink: 'var(--text-base)',
        subdued: 'var(--text-subdued)',
        negative: 'var(--text-negative)',
        warning: 'var(--text-warning)',
        announcement: 'var(--text-announcement)',
      },
      fontFamily: {
        sans: ['var(--font-body)'],
        display: ['var(--font-title)'],
      },
      borderRadius: {
        pill: 'var(--radius-full-pill)',
        card: 'var(--radius-comfortable)',
      },
      boxShadow: {
        elevated: 'var(--shadow-medium)',
        dialog: 'var(--shadow-heavy)',
      },
      transitionDuration: {
        DEFAULT: '200ms',
      },
      transitionTimingFunction: {
        DEFAULT: 'ease',
      },
    },
  },
  plugins: [],
}
