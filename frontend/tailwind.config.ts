import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic": "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
      colors: {
        brand: {
          50: "#f0f5ff",
          100: "#e0ebff",
          200: "#c7dcff",
          300: "#9fc0ff",
          400: "#6b9aff",
          500: "#3b6eff",
          600: "#254ce6",
          700: "#1d3bb3",
          800: "#1d3391",
          900: "#1e2e73",
          950: "#111845",
        },
        slate: {
          50: "var(--slate-50)",
          100: "var(--slate-100)",
          200: "var(--slate-200)",
          300: "var(--slate-300)",
          400: "var(--slate-400)",
          500: "var(--slate-500)",
          600: "var(--slate-600)",
          700: "var(--slate-700)",
          800: "var(--slate-800)",
          900: "var(--slate-900)",
          950: "var(--slate-950)",
        }
      },
    },
  },
  plugins: [],
};
export default config;
