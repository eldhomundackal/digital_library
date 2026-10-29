import { useForm, Controller } from 'react-hook-form'
import { useBroadcastNotification } from '@/hooks/admin/useAdminNotifications'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'

interface BroadcastForm {
  title: string
  message: string
  type: string
  target_role: string
}

const typeOptions = [
  { value: 'INFO', label: 'Info' },
  { value: 'WARNING', label: 'Warning' },
  { value: 'SUCCESS', label: 'Success' },
]

const roleOptions = [
  { value: '', label: 'All users' },
  { value: 'reader', label: 'Readers only' },
  { value: 'publisher', label: 'Publishers only' },
]

export default function AdminNotificationsPage() {
  const broadcast = useBroadcastNotification()
  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<BroadcastForm>({
    defaultValues: { type: 'INFO', target_role: '' },
  })

  function onSubmit(data: BroadcastForm) {
    broadcast.mutate(
      { title: data.title, message: data.message, type: data.type, target_role: data.target_role || undefined },
      { onSuccess: () => reset() },
    )
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Broadcast Notification</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 rounded-card border border-gray-200 bg-white p-6">
        <Input label="Title" error={errors.title?.message} {...register('title', { required: 'Title is required' })} />
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Message</label>
          <textarea
            className="w-full rounded-btn border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            rows={3}
            {...register('message', { required: true })}
          />
        </div>
        <Controller
          control={control}
          name="type"
          render={({ field }) => (
            <Select label="Type" options={typeOptions} value={field.value} onChange={(e) => field.onChange(e.target.value)} />
          )}
        />
        <Controller
          control={control}
          name="target_role"
          render={({ field }) => (
            <Select label="Target audience" options={roleOptions} value={field.value} onChange={(e) => field.onChange(e.target.value)} />
          )}
        />
        <div className="flex justify-end">
          <Button type="submit" loading={broadcast.isPending}>Broadcast</Button>
        </div>
      </form>
    </div>
  )
}
