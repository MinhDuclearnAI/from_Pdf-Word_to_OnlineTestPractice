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
          50: "#EAF2FF",
          100: "#D4E5FF",
          200: "#A9CBFF",
          300: "#7AABFF",
          400: "#4C8DFF",
          500: "#0052CC",
          600: "#0043A6",
          700: "#003380",
          800: "#002459",
          900: "#001433",
          950: "#000A1A",
        },
      },
    },
  },
  plugins: [],
};
export default config;
