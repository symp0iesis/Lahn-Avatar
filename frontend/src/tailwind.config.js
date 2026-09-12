/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}", // if you have a components folder
  ],
  theme: {
  	extend: {
  		  fontFamily: {
            poetic: ['Inter', '"Helvetica Neue"', 'Helvetica', 'Arial', 'sans-serif'],
            display: ['Gloock', 'Inter', 'sans-serif'],
            data: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
  		  },
        textShadow: {
          sm: '0 1px 2px var(--tw-shadow-color)',
          DEFAULT: '0 2px 4px var(--tw-shadow-color)',
          md: '0 4px 6px var(--tw-shadow-color)',
          lg: '0 8px 16px var(--tw-shadow-color)',
        },
        dropShadow: {
          'text': '0 1px 1px rgba(0, 0, 0, 0.8)',
          'text-md': '0 2px 2px rgba(0, 0, 0, 0.8)',
          'text-lg': '0 3px 3px rgba(0, 0, 0, 0.8)',
        },
  		animation: {
  			ripple: 'ripple 3s ease-in-out infinite',
  			breathe: 'breathe 4s ease-in-out infinite'
  		},
  		keyframes: {
  			ripple: {
  				'0%, 100%': {
  					transform: 'scale(1)',
  					opacity: '0.9'
  				},
  				'50%': {
  					transform: 'scale(1.02)',
  					opacity: '1'
  				}
  			},
  			breathe: {
  				'0%, 100%': {
  					transform: 'scale(1)'
  				},
  				'50%': {
  					transform: 'scale(1.05)'
  				}
  			}
  		},
  		borderRadius: {
  			lg: 'var(--radius)',
  			md: 'calc(var(--radius) - 2px)',
  			sm: 'calc(var(--radius) - 4px)'
  		},
  		colors: {
        /* garden palette */
        garden: {
          paper:    '#F5F1E8',
          paper2:   '#EDE7DA',
          ink:      '#2B2B24',
          inksoft:  '#6B675C',
          line:     '#C9C2B2',
          moss:     '#4A6741',
          mossdeep: '#3A5233',
          mosstint: '#E7EBDD',
          water:    '#3E7CB1',
          watertint:'#DDE7EE',
          clay:     '#9A3B26',
          amber:    '#B45309',
        },
        /* shadcn tokens (hex vars now — no hsl wrapper) */
  			background: 'var(--background)',
  			foreground: 'var(--foreground)',
  			card: {
  				DEFAULT: 'var(--card)',
  				foreground: 'var(--card-foreground)'
  			},
  			popover: {
  				DEFAULT: 'var(--popover)',
  				foreground: 'var(--popover-foreground)'
  			},
  			primary: {
  				DEFAULT: 'var(--primary)',
  				foreground: 'var(--primary-foreground)'
  			},
  			secondary: {
  				DEFAULT: 'var(--secondary)',
  				foreground: 'var(--secondary-foreground)'
  			},
  			muted: {
  				DEFAULT: 'var(--muted)',
  				foreground: 'var(--muted-foreground)'
  			},
  			accent: {
  				DEFAULT: 'var(--accent)',
  				foreground: 'var(--accent-foreground)'
  			},
  			destructive: {
  				DEFAULT: 'var(--destructive)',
  				foreground: 'var(--destructive-foreground)'
  			},
  			border: 'var(--border)',
  			input: 'var(--input)',
  			ring: 'var(--ring)',
  			chart: {
  				'1': 'var(--chart-1)',
  				'2': 'var(--chart-2)',
  				'3': 'var(--chart-3)',
  				'4': 'var(--chart-4)',
  				'5': 'var(--chart-5)'
  			}
  		}
  	}
  },
  plugins: [
    require("tailwindcss-animate"),
    function ({ addUtilities, theme }) {
      const newUtilities = {
        '.text-shadow-sm': {
          textShadow: theme('textShadow.sm'),
        },
        '.text-shadow': {
          textShadow: theme('textShadow.DEFAULT'),
        },
        '.text-shadow-md': {
          textShadow: theme('textShadow.md'),
        },
        '.text-shadow-lg': {
          textShadow: theme('textShadow.lg'),
        },
      }
      addUtilities(newUtilities, ['responsive', 'hover'])
    }
  ],
};