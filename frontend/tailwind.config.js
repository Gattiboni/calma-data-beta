/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#2A8C99",
        secondary: "#A8C6A6",
        surface: "#FAFAF7",
        offwhite: "#FAFAF7",
        white: "#FFFFFF",
        darkgray: "#555251",
        elegant: "#6D6A69"
      },
      fontFamily: {
        heading: ['Lora', 'serif'],
        body: ['Radley', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif']
      },
      borderRadius: {
        DEFAULT: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px'
      },
      boxShadow: {
        soft: '0 2px 10px rgba(0,0,0,0.06)',
        softer: '0 1px 4px rgba(0,0,0,0.04)'
      }
    }
  },
  plugins: []
}