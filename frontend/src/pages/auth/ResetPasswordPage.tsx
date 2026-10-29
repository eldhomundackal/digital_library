import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { z } from 'zod'
import { OTPInput } from '@/components/ui/OTPInput'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { resetPasswordSchema } from '@/utils/validators'
import { useVerifyResetOTP, useResetPassword } from '@/hooks/useAuth'

type ResetForm = z.infer<typeof resetPasswordSchema>

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? ''
  const navigate = useNavigate()
  const [otp, setOtp] = useState('')
  const [sessionToken, setSessionToken] = useState<string | null>(null)

  const verifyOTP = useVerifyResetOTP()
  const resetPassword = useResetPassword()

  const { register, handleSubmit, formState: { errors } } = useForm<ResetForm>({
    resolver: zodResolver(resetPasswordSchema),
  })

  function handleVerifyOTP(e: React.FormEvent) {
    e.preventDefault()
    if (otp.length < 6) return
    verifyOTP.mutate({ email, otp }, {
      onSuccess: (data) => setSessionToken(data.reset_session_token),
    })
  }

  function onSubmitReset(data: ResetForm) {
    if (!sessionToken) return
    resetPassword.mutate(
      { reset_session_token: sessionToken, new_password: data.password, confirm_password: data.confirm_password },
      { onSuccess: () => navigate('/login') },
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm rounded-card bg-white p-8 shadow-sm">
        {!sessionToken ? (
          <>
            <h1 className="mb-1 font-heading text-2xl font-bold text-gray-900">Enter reset code</h1>
            <p className="mb-6 text-sm text-gray-500">
              We sent a code to <strong>{email}</strong>
            </p>
            <form onSubmit={handleVerifyOTP} className="space-y-4">
              <div className="flex justify-center">
                <OTPInput value={otp} onChange={setOtp} length={6} />
              </div>
              <Button type="submit" fullWidth loading={verifyOTP.isPending} disabled={otp.length < 6}>
                Verify code
              </Button>
            </form>
          </>
        ) : (
          <>
            <h1 className="mb-1 font-heading text-2xl font-bold text-gray-900">New password</h1>
            <p className="mb-6 text-sm text-gray-500">Choose a strong new password.</p>
            <form onSubmit={handleSubmit(onSubmitReset)} className="space-y-4">
              <Input
                label="New password"
                type="password"
                autoComplete="new-password"
                error={errors.password?.message}
                {...register('password')}
              />
              <Input
                label="Confirm password"
                type="password"
                autoComplete="new-password"
                error={errors.confirm_password?.message}
                {...register('confirm_password')}
              />
              <Button type="submit" fullWidth loading={resetPassword.isPending}>
                Reset password
              </Button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
