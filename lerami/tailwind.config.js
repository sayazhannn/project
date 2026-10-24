/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#F6F0E8',
        ink: '#231A17',
        accent: '#9A4A3A',
        sand: '#E9DFD3',
        mute: '#6B5F58',
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans: ['Manrope', 'system-ui', 'sans-serif'],
      },
      borderRadius: { DEFAULT: '2px' },
    },
  },
  plugins: [],
}
