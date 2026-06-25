import { motion } from 'framer-motion'
import { useHistoryStats } from '../hooks/useNexus'

export default function StatsDashboard() {
  const { data: stats, isLoading } = useHistoryStats()

  if (isLoading) {
    return <div className="h-40 rounded-xl shimmer-bg" />
  }

  if (!stats || stats.total_solves === 0) {
    return (
      <div className="text-[12.5px] text-[var(--color-ink-faint)] text-center py-8">
        No solves yet — stats will appear here once you run some.
      </div>
    )
  }

  const entries = Object.entries(stats.per_problem).sort((a, b) => b[1].total_solves - a[1].total_solves)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-xl border border-[var(--color-border)] p-3 text-center">
          <div className="text-[20px] font-semibold text-[var(--color-ink)] font-[var(--font-display)]">
            {stats.total_solves}
          </div>
          <div className="text-[10.5px] text-[var(--color-ink-faint)] mt-0.5">total solves</div>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] p-3 text-center">
          <div className="text-[20px] font-semibold font-[var(--font-display)]" style={{ color: 'var(--color-teal)' }}>
            {(stats.overall_success_rate * 100).toFixed(0)}%
          </div>
          <div className="text-[10.5px] text-[var(--color-ink-faint)] mt-0.5">success rate</div>
        </div>
        <div className="rounded-xl border border-[var(--color-border)] p-3 text-center">
          <div className="text-[20px] font-semibold text-[var(--color-ink)] font-[var(--font-display)]">
            {entries.length}
          </div>
          <div className="text-[10.5px] text-[var(--color-ink-faint)] mt-0.5">problems tried</div>
        </div>
      </div>

      <div className="space-y-2">
        {entries.map(([problemId, s], i) => (
          <motion.div
            key={problemId}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
          >
            <div className="flex items-center justify-between text-[11.5px] mb-1">
              <span className="text-[var(--color-ink)] font-[var(--font-mono)]">{problemId}</span>
              <span className="text-[var(--color-ink-faint)]">
                {s.total_solves} run{s.total_solves === 1 ? '' : 's'} · avg {s.avg_attempts ?? '–'} attempts
              </span>
            </div>
            <div className="h-2 rounded-full bg-[var(--color-surface-2)] overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${s.success_rate * 100}%` }}
                transition={{ duration: 0.6, delay: i * 0.04, ease: 'easeOut' }}
                className="h-full rounded-full"
                style={{
                  background: s.success_rate > 0.7 ? 'var(--color-teal)' : s.success_rate > 0.3 ? 'var(--color-amber)' : 'var(--color-rose)',
                }}
              />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
