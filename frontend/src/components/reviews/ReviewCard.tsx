import { Avatar } from '@/components/ui/Avatar'
import { StarRating } from '@/components/ui/StarRating'
import { formatRelativeTime } from '@/utils/formatters'
import type { ReviewResponse } from '@/types/review'

interface ReviewCardProps {
  review: ReviewResponse
}

export function ReviewCard({ review }: ReviewCardProps) {
  return (
    <div className="rounded-card border border-gray-200 bg-white p-4">
      <div className="flex items-start gap-3">
        <Avatar src={review.user.avatar} name={review.user.name} size="sm" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-medium text-gray-900">{review.user.name}</span>
            <span className="shrink-0 text-xs text-gray-400">{formatRelativeTime(review.created_at)}</span>
          </div>
          {review.rating != null && (
            <StarRating value={review.rating} readOnly size="sm" className="mt-1" />
          )}
          {review.comment && (
            <p className="mt-2 text-sm text-gray-700">{review.comment}</p>
          )}
        </div>
      </div>
      {review.replies && review.replies.length > 0 && (
        <ul className="mt-3 space-y-2 border-t pl-10 pt-3">
          {review.replies.map((reply) => (
            <li key={reply.reply_id} className="rounded bg-gray-50 px-3 py-2 text-sm text-gray-700">
              <span className="font-medium text-primary">{reply.user.name}: </span>
              {reply.comment}
              <span className="ml-2 text-xs text-gray-400">{formatRelativeTime(reply.created_at)}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
