import { useRef, useState } from 'react'
import { cn } from '@/utils/cn'
import { formatFileSize } from '@/utils/formatters'
import { validateFile, type FILE_LIMITS } from '@/utils/validators'

interface FileUploadProps {
  type: keyof typeof FILE_LIMITS
  value?: File | null
  onChange: (file: File | null) => void
  error?: string
  label?: string
  hint?: string
  accept?: string
  disabled?: boolean
}

export function FileUpload({
  type,
  value,
  onChange,
  error,
  label,
  hint,
  accept,
  disabled,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [localError, setLocalError] = useState<string | null>(null)

  const displayError = error ?? localError

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    if (!file) {
      onChange(null)
      return
    }
    const validationError = validateFile(file, type)
    if (validationError) {
      setLocalError(validationError)
      e.target.value = ''
      return
    }
    setLocalError(null)
    onChange(file)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files?.[0] ?? null
    if (!file) return
    const validationError = validateFile(file, type)
    if (validationError) {
      setLocalError(validationError)
      return
    }
    setLocalError(null)
    onChange(file)
  }

  return (
    <div className="flex flex-col gap-1">
      {label && <p className="text-sm font-medium text-gray-700">{label}</p>}
      <div
        onClick={() => !disabled && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className={cn(
          'flex cursor-pointer flex-col items-center justify-center rounded-card border-2 border-dashed p-6 text-center transition-colors',
          'hover:border-primary hover:bg-primary/5',
          displayError ? 'border-red-400' : 'border-gray-300',
          disabled && 'cursor-not-allowed opacity-50',
          value && 'border-primary bg-primary/5',
        )}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept={accept}
          disabled={disabled}
          onChange={handleChange}
        />
        {value ? (
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-sm text-gray-700">{value.name}</span>
            <span className="text-xs text-gray-400">({formatFileSize(value.size)})</span>
            <button
              type="button"
              onClick={(e) => { e.stopPropagation(); onChange(null) }}
              className="ml-2 text-gray-400 hover:text-red-600"
            >
              ×
            </button>
          </div>
        ) : (
          <>
            <svg className="mb-2 h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-sm text-gray-600">
              <span className="font-medium text-primary">Click to upload</span> or drag and drop
            </p>
            {hint && <p className="mt-1 text-xs text-gray-400">{hint}</p>}
          </>
        )}
      </div>
      {displayError && <p className="text-xs text-red-600">{displayError}</p>}
    </div>
  )
}
