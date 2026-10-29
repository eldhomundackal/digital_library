export interface ReviewResponse {
  review_id: string
  book_id: string
  user: { user_id: string; name: string; avatar: string | null }
  rating: number | null
  comment: string | null
  is_publisher_response: boolean
  replies: ReplyResponse[]
  created_at: string
  updated_at: string
}

export interface ReplyResponse {
  reply_id: string
  user: { user_id: string; name: string; avatar: string | null }
  comment: string
  is_publisher_response: boolean
  created_at: string
}

export interface SubmitReviewRequest {
  rating?: number
  comment?: string
}

export interface BookReviewsResponse {
  reviews: ReviewResponse[]
  total: number
  page: number
  limit: number
  pages: number
  summary: { average_rating: number; total_reviews: number; rating_distribution: Record<string, number> }
}
