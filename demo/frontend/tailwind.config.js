/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'ops-dark': '#0f172a',
        'ops-panel': '#1e293b',
        'ops-border': '#334155',
        'ops-accent': '#38bdf8',
        'ops-green': '#4ade80',
        'ops-yellow': '#fbbf24',
        'ops-red': '#f87171',
        'ops-purple': '#a78bfa',
      },
    },
  },
  plugins: [],
}
