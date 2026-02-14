/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base colors - deep space aesthetic
        'astro-bg': '#0a0e1a',           // Deep space background
        'astro-surface': '#131720',       // Panel/card backgrounds
        'astro-elevated': '#1a1f2e',      // Elevated elements

        // Borders and dividers
        'astro-border': '#1e293b',        // Subtle borders
        'astro-border-focus': '#334155',  // Focused borders

        // Text hierarchy
        'astro-text': '#e2e8f0',          // Primary text
        'astro-text-muted': '#94a3b8',    // Secondary text
        'astro-text-dim': '#64748b',      // Tertiary text

        // Accent colors - minimal, purposeful
        'astro-accent': '#3b82f6',        // Primary actions (blue, not cyan)
        'astro-accent-hover': '#60a5fa',  // Hover states

        // Status colors
        'astro-success': '#10b981',       // Success states
        'astro-warning': '#f59e0b',       // Warnings
        'astro-error': '#ef4444',         // Errors
        'astro-info': '#06b6d4',          // Info (subtle cyan, sparingly)
      },
    },
  },
  plugins: [],
}
