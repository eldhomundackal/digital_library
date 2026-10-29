export interface NotificationItem {
  notification_id: string
  type: string
  title: string
  message: string
  is_read: boolean
  link: string | null
  created_at: string
}

export interface NotificationListResponse {
  items: NotificationItem[]
  total: number
  unread_count: number
  page: number
  limit: number
  pages: number
}
