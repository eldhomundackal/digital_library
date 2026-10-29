export interface DownloadResponse {
  download_url: string
  expires_at: string
  book: { book_id: string; title: string; file_name: string }
  download_limits: {
    daily_remaining: number
    monthly_remaining: number
    daily_resets_at: string
    monthly_resets_at: string
  }
}

export interface DownloadHistoryItem {
  book_id: string
  title: string
  thumbnail: string | null
  downloaded_at: string
  is_archived: boolean
}
