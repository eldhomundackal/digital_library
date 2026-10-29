import { useRef, useState } from 'react'
import { cn } from '@/utils/cn'

interface OTPInputProps {
  length?: number
  value: string
  onChange: (value: string) => void
  error?: string
  disabled?: boolean
}

export function OTPInput({ length = 6, value, onChange, error, disabled }: OTPInputProps) {
  const [focused, setFocused] = useState<number | null>(null)
  const inputs = useRef<(HTMLInputElement | null)[]>([])

  const digits = value.padEnd(length, '').slice(0, length).split('')

  function handleChange(index: number, char: string) {
    const digit = char.replace(/\D/g, '').slice(-1)
    const next = digits.map((d, i) => (i === index ? digit : d))
    onChange(next.join('').replace(/ /g, ''))
    if (digit && index < length - 1) {
      inputs.current[index + 1]?.focus()
    }
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputs.current[index - 1]?.focus()
    }
  }

  function handlePaste(e: React.ClipboardEvent) {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, length)
    onChange(pasted)
    const nextIndex = Math.min(pasted.length, length - 1)
    inputs.current[nextIndex]?.focus()
  }

  return (
    <div>
      <div className="flex gap-2">
        {digits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => {
              inputs.current[i] = el
            }}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit === ' ' ? '' : digit}
            disabled={disabled}
            onFocus={() => setFocused(i)}
            onBlur={() => setFocused(null)}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            onPaste={handlePaste}
            className={cn(
              'h-12 w-10 rounded-btn border text-center text-lg font-semibold',
              'focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary',
              'disabled:cursor-not-allowed disabled:bg-gray-50',
              focused === i && 'border-primary',
              error ? 'border-red-500' : 'border-gray-300',
            )}
          />
        ))}
      </div>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
