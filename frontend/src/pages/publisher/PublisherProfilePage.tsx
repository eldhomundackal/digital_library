import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { usePublisherProfile, useUpdatePublisherProfile, useUploadPublisherLogo } from '@/hooks/usePublisher'
import { Avatar } from '@/components/ui/Avatar'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'

interface ProfileForm {
  display_name: string
  bio: string
  website: string
  twitter: string
  linkedin: string
}

export default function PublisherProfilePage() {
  const { data: publisher, isLoading } = usePublisherProfile()
  const update = useUpdatePublisherProfile()
  const uploadLogo = useUploadPublisherLogo()

  const { register, handleSubmit, reset } = useForm<ProfileForm>()

  useEffect(() => {
    if (publisher) {
      const p = publisher.profile
      reset({
        display_name: p.display_name,
        bio: p.bio ?? '',
        website: p.website ?? '',
        twitter: p.social_links.twitter ?? '',
        linkedin: p.social_links.linkedin ?? '',
      })
    }
  }, [publisher, reset])

  if (isLoading) return <Skeleton className="h-64 w-full rounded-card" />
  if (!publisher) return null

  const p = publisher.profile

  function onSubmit(data: ProfileForm) {
    update.mutate({
      display_name: data.display_name,
      bio: data.bio,
      website: data.website,
      social_links: { twitter: data.twitter, linkedin: data.linkedin },
    })
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Publisher Profile</h1>

      <div className="mb-6 flex items-center gap-4">
        <Avatar src={p.logo} name={p.display_name} size="xl" />
        <div>
          <p className="font-medium text-gray-900">{p.display_name}</p>
          <label className="mt-1 block cursor-pointer text-sm text-primary hover:underline">
            Change logo
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadLogo.mutate(f) }}
            />
          </label>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 rounded-card border border-gray-200 bg-white p-6">
        <Input label="Display name" {...register('display_name')} />
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Bio</label>
          <textarea
            className="w-full rounded-btn border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            rows={3}
            {...register('bio')}
          />
        </div>
        <Input label="Website" type="url" placeholder="https://" {...register('website')} />
        <Input label="Twitter URL" type="url" placeholder="https://twitter.com/…" {...register('twitter')} />
        <Input label="LinkedIn URL" type="url" placeholder="https://linkedin.com/in/…" {...register('linkedin')} />
        <div className="flex justify-end">
          <Button type="submit" loading={update.isPending}>Save changes</Button>
        </div>
      </form>
    </div>
  )
}
