/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fey: {
          bg: "#08080a",
          surface: "#0f0f12",
          "surface-elevated": "#15151a",
          "surface-highlight": "#1c1c22",
          border: "rgba(255, 255, 255, 0.08)",
          "border-subtle": "rgba(255, 255, 255, 0.04)",
          "border-hover": "rgba(255, 255, 255, 0.16)",
          muted: "#71717a",
          text: "#f4f4f5",
          accent: "#ef4444",
        },
      },
      boxShadow: {
        "fey-card": "inset 0 1px 0 0 rgba(255, 255, 255, 0.06), 0 4px 20px -2px rgba(0, 0, 0, 0.5)",
        "fey-card-hover": "inset 0 1px 0 0 rgba(255, 255, 255, 0.10), 0 8px 30px -4px rgba(0, 0, 0, 0.6)",
        "fey-glass": "inset 0 1px 0 0 rgba(255, 255, 255, 0.08)",
        "fey-glow": "0 0 25px -4px rgba(239, 68, 68, 0.2)",
      },
      letterSpacing: {
        tighter: "-0.03em",
        tight: "-0.015em",
      },
    },
  },
  plugins: [],
}
