import { z } from 'zod'

export const loginSchema = z.object({
  email:    z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

export const registerSchema = z.object({
  email:            z.string().email('Enter a valid email'),
  password:         z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
  first_name:       z.string().min(1, 'First name is required'),
  last_name:        z.string().min(1, 'Last name is required'),
  role:             z.enum(['reader', 'publisher']),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export const forgotPasswordSchema = z.object({
  email: z.string().email('Enter a valid email'),
})

export const resetPasswordSchema = z.object({
  password:         z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export const reviewSchema = z.object({
  rating:  z.number().min(1).max(5),
  comment: z.string().max(2000).optional(),
})

export const uploadBookSchema = z.object({
  title:            z.string().min(1, 'Title is required'),
  description:      z.string().min(1, 'Description is required'),
  category_id:      z.number().min(1, 'Select a category'),
  language_id:      z.number().min(1, 'Select a language'),
  version_label:    z.string().min(1, 'Version label is required (e.g. 1.0)'),
  isbn:             z.string().optional(),
  page_count:       z.number().positive().optional(),
  publication_year: z.number().min(1000).max(2100).optional(),
})

export const updateProfileSchema = z.object({
  first_name:  z.string().min(1).optional(),
  last_name:   z.string().min(1).optional(),
  bio:         z.string().max(500).optional(),
  occupation:  z.string().optional(),
  gender:      z.string().optional(),
  date_of_birth: z.string().optional(),
})

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password:     z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((d) => d.new_password === d.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

export const FILE_LIMITS = {
  book_pdf:  50 * 1024 * 1024,
  thumbnail: 2  * 1024 * 1024,
  kyc_doc:   10 * 1024 * 1024,
  avatar:    2  * 1024 * 1024,
} as const

export const ALLOWED_TYPES = {
  book_pdf:  ['application/pdf'],
  thumbnail: ['image/jpeg', 'image/png', 'image/webp'],
  kyc_doc:   ['application/pdf'],
  avatar:    ['image/jpeg', 'image/png', 'image/webp'],
} as const

export function validateFile(file: File, type: keyof typeof FILE_LIMITS): string | null {
  const allowed = ALLOWED_TYPES[type] as readonly string[]
  if (!allowed.includes(file.type)) {
    return `Invalid file type. Accepted: ${allowed.join(', ')}`
  }
  if (file.size > FILE_LIMITS[type]) {
    return `File too large. Max: ${FILE_LIMITS[type] / 1024 / 1024} MB`
  }
  return null
}
