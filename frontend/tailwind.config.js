/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      keyframes: {
        shake: {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-5px)' },
          '75%': { transform: 'translateX(5px)' },
        }
      },
      animation: {
        shake: 'shake 0.2s ease-in-out 0s 2',
      },
      colors: {
        brand: {
          50: '#f5f7ff',
          100: '#ebf0fe',
          200: '#ced9fd',
          300: '#adc0fc',
          400: '#8ca7fa',
          500: '#6b8ef9',
          600: '#5671c7',
          700: '#405595',
          800: '#2b3964',
          900: '#151c32',
        },
      },
    },
  },
  plugins: [],
}
