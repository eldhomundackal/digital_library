import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { registerSchema } from '@/utils/validators'
import { useRegister } from '@/hooks/useAuth'

type RegisterForm = z.infer<typeof registerSchema>

const roleOptions = [
  { value: 'reader', label: 'Reader — browse & download books' },
  { value: 'publisher', label: 'Publisher — publish & sell books' },
]

export default function RegisterPage() {
  const navigate = useNavigate()
  const registerMutation = useRegister()

  const { register, handleSubmit, formState: { errors } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: 'reader' },
  })

  function onSubmit(data: RegisterForm) {
    registerMutation.mutate(data, {
      onSuccess: (res) => {
        navigate(`/verify-email?email=${encodeURIComponent(res.email)}`)
      },
    })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-8">
      <div className="w-full max-w-md rounded-card bg-white p-8 shadow-sm">
        <h1 className="mb-1 font-heading text-2xl font-bold text-gray-900">Create account</h1>
        <p className="mb-6 text-sm text-gray-500">Join Libraflow today</p>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First name"
              error={errors.first_name?.message}
              {...register('first_name')}
            />
            <Input
              label="Last name"
              error={errors.last_name?.message}
              {...register('last_name')}
            />
          </div>
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email')}
          />
          <Input
            label="Password"
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
          <Select
            label="I want to…"
            options={roleOptions}
            error={errors.role?.message}
            {...register('role')}
          />
          <Button type="submit" fullWidth loading={registerMutation.isPending}>
            Create account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500">
          Already have an account?{' '}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
