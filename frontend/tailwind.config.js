/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}", // if you have a components folder
  ],
  theme: {
    extend: {
      fontFamily: {
        //poetic: ['"Georgia"', 'serif'], // or any poetic/serif font you choose
        poetic: ['"Gloock"', 'serif'],
      },
      animation: {
        ripple: "ripple 3s ease-in-out infinite",
        breathe: "breathe 4s ease-in-out infinite",
      },
      keyframes: {
        ripple: {
          "0%, 100%": { transform: "scale(1)", opacity: "0.9" },
          "50%": { transform: "scale(1.02)", opacity: "1" },
        },
        breathe: {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.05)" },
        },
      },
    },
  },
  plugins: [],
};
