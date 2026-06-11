import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#1A2B4A",
          light: "#243d6a",
          accent: "#C17F3E",
        },
      },
    },
  },
  plugins: [],
};

export default config;
