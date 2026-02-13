/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'tron-bg': '#0a0e1a',
        'tron-panel': '#111827',
        'tron-border': '#1e3a5f',
        'tron-accent': '#00d4ff',
        'tron-text': '#e0f2ff',
      },
    },
  },
  plugins: [],
}
