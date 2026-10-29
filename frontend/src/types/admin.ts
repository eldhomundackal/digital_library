export interface AdminDashboardStats {
  total_users: number
  total_books: number
  total_downloads: number
  pending_kyc: number
  pending_books: number
  active_publishers: number
}

export interface PendingAction {
  type: 'kyc' | 'book'
  id: string
  title: string
  submitted_by: string
  submitted_at: string
}

export interface ActivityFeedItem {
  activity_id: string
  action: string
  entity_type: string
  entity_id: string
  performed_by: string
  created_at: string
}

export interface AuditLogItem {
  audit_id: string
  action: string
  entity_type: string
  entity_id: string
  performed_by: string
  ip_address: string
  created_at: string
  metadata: Record<string, unknown>
}

export interface AdminUserItem {
  user_id: string
  email: string
  role: string
  is_active: boolean
  is_email_verified: boolean
  created_at: string
  display_name: string | null
  kyc_status: string | null
}
