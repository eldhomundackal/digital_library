export interface KYCDocument {
  document_id: string
  document_type: string
  file_url: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  rejection_reason: string | null
  uploaded_at: string
}

export interface KYCResponse {
  kyc_id: string
  status: 'INCOMPLETE' | 'PENDING' | 'APPROVED' | 'REJECTED' | 'RESUBMITTED'
  documents: KYCDocument[]
  submitted_at: string | null
  reviewed_at: string | null
  rejection_reason: string | null
}
