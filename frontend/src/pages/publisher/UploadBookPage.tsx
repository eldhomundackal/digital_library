import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { FileUpload } from '@/components/ui/FileUpload'
import { uploadBookSchema } from '@/utils/validators'
import { useUploadBook } from '@/hooks/useBooks'
import { useCategories, useLanguages } from '@/hooks/useUtils'

type UploadForm = z.infer<typeof uploadBookSchema>

export default function UploadBookPage() {
  const navigate = useNavigate()
  const upload = useUploadBook()
  const { data: categories } = useCategories()
  const { data: languages } = useLanguages()
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [thumbnail, setThumbnail] = useState<File | null>(null)
  const [pdfError, setPdfError] = useState<string | null>(null)
  const [thumbError, setThumbError] = useState<string | null>(null)

  const { register, handleSubmit, control, formState: { errors } } = useForm<UploadForm>({
    resolver: zodResolver(uploadBookSchema),
  })

  function onSubmit(data: UploadForm) {
    if (!pdfFile) { setPdfError('PDF is required'); return }
    if (!thumbnail) { setThumbError('Thumbnail is required'); return }
    upload.mutate(
      { ...data, thumbnail, pdf_file: pdfFile, tag_ids: [], new_tags: [], authors: [] },
      { onSuccess: () => navigate('/publisher/books') },
    )
  }

  const categoryOptions = (categories ?? []).map((c) => ({ value: c.id, label: c.name }))
  const languageOptions = (languages ?? []).map((l) => ({ value: l.id, label: l.name }))

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 font-heading text-2xl font-bold text-gray-900">Upload Book</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 rounded-card border border-gray-200 bg-white p-6">
        <Input label="Title" error={errors.title?.message} {...register('title')} />
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Description</label>
          <textarea
            className="w-full rounded-btn border border-gray-300 px-3 py-2 text-sm focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            rows={4}
            {...register('description')}
          />
          {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Controller
            control={control}
            name="category_id"
            render={({ field }) => (
              <Select
                label="Category"
                options={categoryOptions}
                placeholder="Select category"
                error={errors.category_id?.message}
                value={field.value ?? ''}
                onChange={(e) => field.onChange(Number(e.target.value))}
              />
            )}
          />
          <Controller
            control={control}
            name="language_id"
            render={({ field }) => (
              <Select
                label="Language"
                options={languageOptions}
                placeholder="Select language"
                error={errors.language_id?.message}
                value={field.value ?? ''}
                onChange={(e) => field.onChange(Number(e.target.value))}
              />
            )}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          <Input label="Version label" placeholder="1.0" error={errors.version_label?.message} {...register('version_label')} />
          <Input label="ISBN (optional)" {...register('isbn')} />
          <Input label="Publication year" type="number" {...register('publication_year', { valueAsNumber: true })} />
        </div>
        <Input label="Page count (optional)" type="number" {...register('page_count', { valueAsNumber: true })} />

        <FileUpload
          type="thumbnail"
          label="Thumbnail"
          hint="JPG, PNG or WebP — max 2MB"
          value={thumbnail}
          onChange={(f) => { setThumbnail(f); setThumbError(null) }}
          error={thumbError ?? undefined}
        />
        <FileUpload
          type="book_pdf"
          label="PDF file"
          hint="PDF — max 50MB"
          value={pdfFile}
          onChange={(f) => { setPdfFile(f); setPdfError(null) }}
          error={pdfError ?? undefined}
        />

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="ghost" type="button" onClick={() => navigate('/publisher/books')}>Cancel</Button>
          <Button type="submit" loading={upload.isPending}>Upload Book</Button>
        </div>
      </form>
    </div>
  )
}
