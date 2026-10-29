import type { CategorySummary, LanguageSummary, TagSummary } from './common'

export interface AuthorSummary {
  author_id: string
  name: string
  avatar: string | null
}

export interface BookListItem {
  book_id: string
  title: string
  slug: string
  thumbnail: string | null
  authors: AuthorSummary[]
  category: CategorySummary
  language: LanguageSummary
  average_rating: number
  review_count: number
  download_count: number
  publication_year: number | null
  created_at: string
}

export interface BookDetailResponse {
  book_id: string
  title: string
  slug: string
  description: string
  thumbnail: string | null
  isbn: string | null
  page_count: number | null
  publication_year: number | null
  version_label: string
  status: string
  authors: AuthorSummary[]
  category: CategorySummary
  language: LanguageSummary
  tags: TagSummary[]
  average_rating: number
  review_count: number
  download_count: number
  publisher: PublisherBrief
  created_at: string
  updated_at: string
}

export interface PublisherBrief {
  user_id: string
  display_name: string
  logo: string | null
  is_verified: boolean
}

export interface BookFilters {
  search?: string
  category_id?: number
  tag_id?: number
  language_id?: number
  publication_year?: number
  sort_by?: 'latest' | 'popular' | 'rating'
  page?: number
  limit?: number
}

export interface CreateBookPayload {
  title: string
  description: string
  category_id: number
  language_id: number
  version_label: string
  isbn?: string
  page_count?: number
  publication_year?: number
  tag_ids: number[]
  new_tags: string[]
  authors: { name: string; bio?: string }[]
  thumbnail: File
  pdf_file: File
  onProgress?: (event: { loaded: number; total?: number }) => void
}
