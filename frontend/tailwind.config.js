/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      fontFamily: {
        'title': ['Fredoka', 'cursive'],
        'body': ['Nunito', 'sans-serif']
      },
      colors: {
        'ratoncito': {
          'yellow': '#f8cb39',
          'brown': '#ac8623',
          'red': '#ee4337',
          'blue': '#66c5fe',
          'background': '#fff9e8'
        }
      },
      animation: {
        'bounce-soft': 'bounce-soft 2s infinite',
        'pulse-glow': 'pulse-glow 2s infinite'
      },
      keyframes: {
        'bounce-soft': {
          '0%, 100%': {
            transform: 'translateY(0)',
          },
          '50%': {
            transform: 'translateY(-5px)',
          }
        },
        'pulse-glow': {
          '0%, 100%': {
            opacity: '1',
            transform: 'scale(1)'
          },
          '50%': {
            opacity: '0.8',
            transform: 'scale(1.05)'
          }
        }
      }
    },
  },
  plugins: [],
}
