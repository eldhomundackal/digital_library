import type { CategorySummary, CitySummary, CountrySummary, LanguageSummary, TagSummary } from './common'

export interface SocialLinks {
  twitter: string | null
  linkedin: string | null
  facebook: string | null
  instagram: string | null
}

export interface ReaderProfileDetail {
  first_name: string
  last_name: string
  avatar: string | null
  bio: string | null
  date_of_birth: string | null
  gender: string | null
  country: CountrySummary | null
  city: CitySummary | null
  preferred_language: LanguageSummary | null
  preferred_categories: CategorySummary[]
  preferred_tags: TagSummary[]
  occupation: string | null
}

export interface ReaderProfileResponse {
  user_id: string
  email: string
  role: string
  is_email_verified: boolean
  is_active: boolean
  profile_completion: number
  created_at: string
  profile: ReaderProfileDetail
}

export interface PublisherProfileDetail {
  display_name: string
  bio: string | null
  logo: string | null
  website: string | null
  social_links: SocialLinks
  total_books: number
  joined_date: string
  is_verified: boolean
}

export interface PublisherProfileResponse {
  user_id: string
  email: string
  role: string
  is_email_verified: boolean
  is_active: boolean
  kyc_status: string
  created_at: string
  profile: PublisherProfileDetail
}

export interface UpdateReaderProfileRequest {
  first_name?: string
  last_name?: string
  bio?: string
  date_of_birth?: string
  gender?: string
  country_id?: number
  city_id?: number
  language_id?: number
  preferred_category_ids?: number[]
  preferred_tag_ids?: number[]
  occupation?: string
}
