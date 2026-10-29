import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { apiClient, getApiError } from '@/api/client'
import { useAuthStore } from '@/store/authStore'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  VerifyEmailResponse,
  VerifyResetOTPResponse,
} from '@/types/auth'

export function useLogin() {
  const { setAccessToken, setUser } = useAuthStore()
  return useMutation({
    mutationFn: async (payload: LoginRequest) => {
      const { data } = await apiClient.post<LoginResponse>('/auth/login', payload)
      return data
    },
    onSuccess: (data) => {
      setAccessToken(data.access_token)
      setUser(data.user)
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: async (payload: RegisterRequest) => {
      const { data } = await apiClient.post<RegisterResponse>('/auth/register', payload)
      return data
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useVerifyEmail() {
  return useMutation({
    mutationFn: async (payload: { email: string; otp: string }) => {
      const { data } = await apiClient.post<VerifyEmailResponse>('/auth/verify-email', payload)
      return data
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useResendVerification() {
  return useMutation({
    mutationFn: async (email: string) => {
      await apiClient.post('/auth/resend-verification', { email })
    },
    onSuccess: () => toast.success('Verification email sent.'),
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: async (email: string) => {
      await apiClient.post('/auth/forgot-password', { email })
    },
    onSuccess: () => toast.success('OTP sent to your email.'),
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useVerifyResetOTP() {
  return useMutation({
    mutationFn: async (payload: { email: string; otp: string }) => {
      const { data } = await apiClient.post<VerifyResetOTPResponse>('/auth/verify-reset-otp', payload)
      return data
    },
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (payload: {
      reset_session_token: string
      new_password: string
      confirm_password: string
    }) => {
      await apiClient.post('/auth/reset-password', payload)
    },
    onSuccess: () => toast.success('Password reset successfully.'),
    onError: (err) => toast.error(getApiError(err)),
  })
}

export function useLogout() {
  const { logout } = useAuthStore()
  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/auth/logout')
    },
    onSettled: () => {
      logout()
    },
  })
}
