/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "Menlo", "monospace"],
      },
      colors: {
        ink: {
          DEFAULT: "#0a0a0a",
          900: "#0a0a0a",
          800: "#1a1a1a",
          700: "#2a2a2a",
          600: "#525252",
          500: "#737373",
          400: "#a3a3a3",
          300: "#d4d4d4",
          200: "#e5e5e5",
          100: "#f5f5f5",
          50: "#fafafa",
        },
        accent: {
          DEFAULT: "#1a3a8f",
          50: "#eef2fb",
          100: "#dae3f6",
          200: "#b6c8ee",
          500: "#1a3a8f",
          600: "#152e72",
          700: "#102258",
        },
        signal: {
          green: "#15803d",
          amber: "#a16207",
          red: "#b91c1c",
        },
      },
      letterSpacing: {
        tightest: "-0.04em",
      },
      borderRadius: {
        sm: "2px",
        DEFAULT: "4px",
        md: "6px",
        lg: "8px",
      },
      boxShadow: {
        crisp: "0 1px 0 rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.04)",
      },
    },
  },
  plugins: [],
};
