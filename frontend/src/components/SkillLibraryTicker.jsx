import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'

export default function SkillLibraryTicker({ stats, loading }) {
  if (loading) {
    return <div className="h-5 w-48 rounded shimmer-bg" />
  }
  const total = stats?.skill_library?.total_patterns ?? 0
  const byType = stats?.skill_library?.by_bug_type ?? {}
  const topTypes = Object.entries(byType).sort((a, b) => b[1] - a[1]).slice(0, 3)

  return (
    <div className="flex items-center gap-2 text-[12px] text-[var(--color-ink-faint)] font-[var(--font-mono)]">
      <BookOpen size={13} />
      <motion.span key={total} initial={{ opacity: 0.4 }} animate={{ opacity: 1 }}>
        {total} learned bug-fix pattern{total === 1 ? '' : 's'} in memory
      </motion.span>
      {topTypes.length > 0 && (
        <span className="hidden md:inline text-[var(--color-ink-faint)]">
          · most common: {topTypes.map(([type, count]) => `${type} (${count})`).join(', ')}
        </span>
      )}
    </div>
  )
}
