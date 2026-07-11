/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          0: "#08070c",
          1: "#0f0d16",
          2: "#161320",
          3: "#1e1a2b",
          4: "#28233a",
        },
        mood: {
          tired: "#7c93e8",
          stressed: "#f25a7a",
          happy: "#fbbf24",
          excited: "#fb7a3f",
          calm: "#34d9bc",
          anxious: "#d896f0",
          sad: "#8b9fd9",
          bored: "#a39d8f",
          neutral: "#a78bfa",
        },
      },
      fontFamily: {
        vazir: ["Vazirmatn", "Tahoma", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
        display: ["Space Grotesk", "Vazirmatn", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -10px var(--tw-shadow-color)",
        "glow-lg": "0 0 80px -20px var(--tw-shadow-color)",
        "glow-sm": "0 0 20px -8px var(--tw-shadow-color)",
      },
      backdropBlur: {
        xs: "2px",
      },
      animation: {
        "pulse-slow": "pulse-slow 4s ease-in-out infinite",
        float: "float 6s ease-in-out infinite",
        "spin-slow": "spin 18s linear infinite",
        shimmer: "shimmer 2.5s linear infinite",
        "fade-up": "fade-up 0.5s ease-out forwards",
        // Equalizer bars for MusicCard
        "eq-1": "eq 0.95s ease-in-out infinite",
        "eq-2": "eq 0.95s ease-in-out infinite 0.22s",
        "eq-3": "eq 0.95s ease-in-out infinite 0.11s",
        "eq-4": "eq 0.95s ease-in-out infinite 0.33s",
      },
      keyframes: {
        "pulse-slow": {
          "0%, 100%": { opacity: 0.55, transform: "scale(1)" },
          "50%": { opacity: 0.9, transform: "scale(1.06)" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-14px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
        "fade-up": {
          "0%": { opacity: 0, transform: "translateY(10px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        eq: {
          "0%, 100%": { transform: "scaleY(0.3)" },
          "50%": { transform: "scaleY(1)" },
        },
      },
    },
  },
  plugins: [],
};
