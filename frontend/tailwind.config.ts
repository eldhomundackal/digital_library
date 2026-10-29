import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary:           '#1B6B6B',
        'primary-dark':    '#145858',
        'primary-light':   '#1B6B6B15',
        accent:            '#E8A838',
        'accent-dark':     '#B8820A',
        'accent-light':    '#E8A83820',
        background:        '#F8F6F2',
        surface:           '#FFFFFF',
        'surface-muted':   '#F0EDE8',
        text:              '#1C1C1E',
        'text-secondary':  '#3D3D3F',
        muted:             '#6B7280',
        'muted-light':     '#9CA3AF',
        border:            '#E5E0D8',
        success:           '#16A34A',
        'success-light':   '#16A34A15',
        danger:            '#DC2626',
        'danger-light':    '#DC262615',
        warning:           '#B8820A',
        'warning-light':   '#E8A83820',
      },
      fontFamily: {
        heading: ['"Playfair Display"', 'Georgia', 'serif'],
        body:    ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '12px',
        btn:  '8px',
        pill: '20px',
      },
    },
  },
  plugins: [],
}

export default config
