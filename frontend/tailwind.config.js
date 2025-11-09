/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        'sans': ['FK Grotesk Neue', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

