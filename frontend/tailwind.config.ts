import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        page: "#F4F7F5",
        ink: "#121614",
        emerald: {
          950: "#12332D",
          900: "#0F5F4A",
          800: "#168A6A",
          50: "#E7F4EF",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 18px 60px rgba(18, 22, 20, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;
