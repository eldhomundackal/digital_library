export interface UserSummary {
  user_id: string
  email: string
  role: string
  is_first_login: boolean
  profile_completion: number | null
  kyc_status: string | null
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: UserSummary
}

export interface RegisterRequest {
  email: string
  password: string
  confirm_password: string
  first_name: string
  last_name: string
  role: 'reader' | 'publisher'
}

export interface RegisterResponse {
  user_id: string
  email: string
  role: string
  is_email_verified: boolean
}

export interface RefreshResponse {
  access_token: string
  expires_in: number
}

export interface VerifyEmailResponse {
  user_id: string
  role: string
  next_step: 'kyc_required' | 'login'
}

export interface VerifyResetOTPResponse {
  reset_session_token: string
  expires_in: number
}
