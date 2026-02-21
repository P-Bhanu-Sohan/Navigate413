module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        crimson: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444', // Primary Red
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        coral: {
          50: '#fef5f3',
          100: '#feddd8',
          200: '#fdbb94',
          300: '#fd9b6e',
          400: '#fc7a48',
          500: '#fb5a22', // Accent Coral
          600: '#e84e1b',
          700: '#d94314',
          800: '#c9380d',
          900: '#8a2506',
        },
      },
    },
  },
  plugins: [],
}

