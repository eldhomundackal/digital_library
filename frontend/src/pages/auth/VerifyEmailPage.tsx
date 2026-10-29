import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { OTPInput } from '@/components/ui/OTPInput'
import { Button } from '@/components/ui/Button'
import { useVerifyEmail, useResendVerification } from '@/hooks/useAuth'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const email = searchParams.get('email') ?? ''
  const [otp, setOtp] = useState('')
  const navigate = useNavigate()
  const verify = useVerifyEmail()
  const resend = useResendVerification()

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (otp.length < 6) return
    verify.mutate({ email, otp }, {
      onSuccess: (data) => {
        if (data.next_step === 'kyc_required') {
          navigate('/publisher/kyc')
        } else {
          navigate('/login')
        }
      },
    })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm rounded-card bg-white p-8 shadow-sm text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
          <svg className="h-7 w-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>
        <h1 className="font-heading text-2xl font-bold text-gray-900">Verify your email</h1>
        <p className="mt-2 text-sm text-gray-500">
          We sent a 6-digit code to <strong>{email}</strong>
        </p>

        <form onSubmit={handleSubmit} className="mt-6">
          <div className="flex justify-center">
            <OTPInput value={otp} onChange={setOtp} length={6} />
          </div>
          <Button type="submit" fullWidth className="mt-6" loading={verify.isPending} disabled={otp.length < 6}>
            Verify Email
          </Button>
        </form>

        <button
          onClick={() => resend.mutate(email)}
          disabled={resend.isPending}
          className="mt-4 text-sm text-primary hover:underline disabled:opacity-50"
        >
          Resend code
        </button>
      </div>
    </div>
  )
}
