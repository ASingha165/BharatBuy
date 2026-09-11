/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Stitch Surface & Palette
        "surface": "#f8f9ff",
        "surface-dim": "#ccdbf3",
        "surface-bright": "#f8f9ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#eff4ff",
        "surface-container": "#e6eeff",
        "surface-container-high": "#dce9ff",
        "surface-container-highest": "#d5e3fc",
        "surface-variant": "#d5e3fc",
        "on-surface": "#0d1c2e",
        "on-surface-variant": "#444653",
        "inverse-surface": "#233144",
        "inverse-on-surface": "#eaf1ff",
        "outline": "#757684",
        "outline-variant": "#c4c5d5",
        "surface-tint": "#3755c3",
        "background": "#f8f9ff",
        "on-background": "#0d1c2e",
        
        // Stitch Primary Actions
        "primary": "#00288e",
        "primary-container": "#1e40af",
        "primary-fixed": "#dde1ff",
        "primary-fixed-dim": "#b8c4ff",
        "on-primary": "#ffffff",
        "on-primary-container": "#a8b8ff",
        "on-primary-fixed": "#001453",
        "on-primary-fixed-variant": "#173bab",
        "inverse-primary": "#b8c4ff",
        
        // Stitch Secondary & Neutrals
        "secondary": "#565e74",
        "secondary-container": "#dae2fd",
        "secondary-fixed": "#dae2fd",
        "secondary-fixed-dim": "#bec6e0",
        "on-secondary": "#ffffff",
        "on-secondary-container": "#5c647a",
        "on-secondary-fixed": "#131b2e",
        "on-secondary-fixed-variant": "#3f465c",
        
        // Stitch Tertiary & Alerts
        "tertiary": "#532a00",
        "tertiary-container": "#743d00",
        "tertiary-fixed": "#ffdcc3",
        "tertiary-fixed-dim": "#ffb77d",
        "on-tertiary": "#ffffff",
        "on-tertiary-container": "#ffa85d",
        "on-tertiary-fixed": "#2f1500",
        "on-tertiary-fixed-variant": "#6e3900",

        // Stitch Error & Warnings
        "error": "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error": "#ffffff",
        "on-error-container": "#93000a",
        
        // Semantic Regulatory States
        "regulatory-verified": "#059669",
        "regulatory-verified-bg": "#ecfdf5",
        "regulatory-verified-border": "#a7f3d0",
        "regulatory-amber": "#d97706",
        "regulatory-amber-bg": "#fffbeb",
        "regulatory-amber-border": "#fde68a",
        "regulatory-error": "#ba1a1a",
        "regulatory-error-bg": "#fef2f2",
        "regulatory-error-border": "#fecaca",

        // Compatibility aliases
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#0284c7',
          600: '#0284c7',
          700: '#0369a1',
          900: '#0c4a6e',
        },
        bis: {
          gold: '#f59e0b',
          blue: '#1e3a8a',
          dark: '#233144',
        }
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
        headline: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
        body: ['var(--font-inter)', 'Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        'space-2xs': '0.125rem',
        'space-xs': '0.25rem',
        'space-sm': '0.5rem',
        'space-md': '0.75rem',
        'space-lg': '1rem',
        'space-xl': '1.5rem',
        'space-2xl': '2rem',
        'layout-sidebar': '18rem',
        'layout-filter-rail': '20rem',
        'layout-gutter': '1rem',
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        'sm': '0.125rem',
        'md': '0.25rem',
        'lg': '0.25rem',
        'xl': '0.5rem',
        '2xl': '0.75rem',
        'full': '9999px',
      }
    },
  },
  plugins: [],
};
