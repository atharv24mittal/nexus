import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, Clock } from 'lucide-react'
import { useHistory } from '../hooks/useNexus'

function timeAgo(unixSeconds) {
  const seconds = Math.floor(Date.now() / 1000 - unixSeconds)
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}

export default function HistoryPanel() {
  const { data: history, isLoading } = useHistory(20)

  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => <div key={i} className="h-12 rounded-lg shimmer-bg" />)}
      </div>
    )
  }

  if (!history || history.length === 0) {
    return (
      <div className="text-[12.5px] text-[var(--color-ink-faint)] text-center py-8">
        No solves yet — run one to start building history.
      </div>
    )
  }

  return (
    <div className="space-y-1.5 max-h-80 overflow-y-auto">
      {history.map((item, i) => (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.03 }}
          className="flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            {item.success ? (
              <CheckCircle2 size={14} className="text-[var(--color-teal)] flex-shrink-0" />
            ) : (
              <XCircle size={14} className="text-[var(--color-rose)] flex-shrink-0" />
            )}
            <span className="text-[12.5px] text-[var(--color-ink)] truncate">{item.problem_id}</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-[var(--color-ink-faint)] font-[var(--font-mono)] flex-shrink-0">
            <span>{item.attempts_count} attempt{item.attempts_count === 1 ? '' : 's'}</span>
            <span className="flex items-center gap-1"><Clock size={10} />{timeAgo(item.created_at)}</span>
          </div>
        </motion.div>
      ))}
    </div>
  )
}
