import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMyProfile, useUpdateProfile, useUploadAvatar, useChangePassword } from '@/hooks/useUsers'
import { Avatar } from '@/components/ui/Avatar'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { updateProfileSchema, changePasswordSchema } from '@/utils/validators'

type ProfileForm = z.infer<typeof updateProfileSchema>
type PasswordForm = z.infer<typeof changePasswordSchema>

export default function ProfilePage() {
  const { data: profile, isLoading } = useMyProfile()
  const updateProfile = useUpdateProfile()
  const uploadAvatar = useUploadAvatar()
  const changePassword = useChangePassword()

  const profileForm = useForm<ProfileForm>({ resolver: zodResolver(updateProfileSchema) })
  const passwordForm = useForm<PasswordForm>({ resolver: zodResolver(changePasswordSchema) })

  useEffect(() => {
    if (profile) {
      profileForm.reset({
        first_name: profile.profile.first_name,
        last_name: profile.profile.last_name,
        bio: profile.profile.bio ?? '',
        occupation: profile.profile.occupation ?? '',
        gender: profile.profile.gender ?? '',
        date_of_birth: profile.profile.date_of_birth ?? '',
      })
    }
  }, [profile, profileForm])

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
        <Skeleton className="mb-4 h-8 w-32" />
        <Skeleton className="h-64 w-full rounded-card" />
      </div>
    )
  }

  if (!profile) return null

  const p = profile.profile
  const name = `${p.first_name} ${p.last_name}`

  return (
    <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">My Profile</h1>

      {/* Avatar */}
      <div className="mb-6 flex items-center gap-4">
        <Avatar src={p.avatar} name={name} size="xl" />
        <div>
          <p className="font-medium text-gray-900">{name}</p>
          <p className="text-sm text-gray-500">{profile.email}</p>
          <label className="mt-2 block cursor-pointer text-sm font-medium text-primary hover:underline">
            Change photo
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) uploadAvatar.mutate(f)
              }}
            />
          </label>
        </div>
      </div>

      {/* Profile form */}
      <form
        onSubmit={profileForm.handleSubmit((data) => updateProfile.mutate(data))}
        className="rounded-card border border-gray-200 bg-white p-6"
      >
        <h2 className="mb-4 font-heading text-lg font-semibold text-gray-900">Personal information</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="First name"
            error={profileForm.formState.errors.first_name?.message}
            {...profileForm.register('first_name')}
          />
          <Input
            label="Last name"
            error={profileForm.formState.errors.last_name?.message}
            {...profileForm.register('last_name')}
          />
        </div>
        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">Bio</label>
          <textarea
            className="w-full rounded-btn border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            rows={3}
            {...profileForm.register('bio')}
          />
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <Input label="Occupation" {...profileForm.register('occupation')} />
          <Input label="Gender" {...profileForm.register('gender')} />
          <Input label="Date of birth" type="date" {...profileForm.register('date_of_birth')} />
        </div>
        <div className="mt-4 flex justify-end">
          <Button type="submit" loading={updateProfile.isPending}>Save changes</Button>
        </div>
      </form>

      {/* Change password */}
      <form
        onSubmit={passwordForm.handleSubmit((data) => {
          changePassword.mutate(data, { onSuccess: () => passwordForm.reset() })
        })}
        className="mt-6 rounded-card border border-gray-200 bg-white p-6"
      >
        <h2 className="mb-4 font-heading text-lg font-semibold text-gray-900">Change password</h2>
        <div className="space-y-4">
          <Input
            label="Current password"
            type="password"
            error={passwordForm.formState.errors.current_password?.message}
            {...passwordForm.register('current_password')}
          />
          <Input
            label="New password"
            type="password"
            error={passwordForm.formState.errors.new_password?.message}
            {...passwordForm.register('new_password')}
          />
          <Input
            label="Confirm new password"
            type="password"
            error={passwordForm.formState.errors.confirm_password?.message}
            {...passwordForm.register('confirm_password')}
          />
        </div>
        <div className="mt-4 flex justify-end">
          <Button type="submit" loading={changePassword.isPending}>Update password</Button>
        </div>
      </form>
    </div>
  )
}
