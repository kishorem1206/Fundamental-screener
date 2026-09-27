/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#030712",
          900: "#0a1020",
          800: "#0f172a",
          700: "#111827",
          600: "#1e293b",
        },
      },
    },
  },
  plugins: [],
};
