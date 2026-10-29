export interface SuccessResponse<T> {
  success: boolean
  message: string | null
  data: T | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface CountrySummary {
  id: number
  name: string
  code: string
}

export interface CitySummary {
  id: number
  name: string
}

export interface LanguageSummary {
  id: number
  name: string
  code: string
}

export interface CategorySummary {
  id: number
  name: string
  slug: string
}

export interface TagSummary {
  id: number
  name: string
  slug: string
}
