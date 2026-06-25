import { motion } from 'framer-motion'
import { Activity } from 'lucide-react'

export default function ComplexityCard({ complexityCheck }) {
  if (!complexityCheck) return null
  const { passed, estimated_exponent, message, samples } = complexityCheck

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: 0.08 }}
      className="rounded-xl border p-3.5"
      style={{
        borderColor: passed ? 'var(--color-teal-dim)' : 'var(--color-rose-dim)',
        background: 'var(--color-surface)',
      }}
    >
      <div className="flex items-start gap-2.5">
        <Activity size={16} className="flex-shrink-0 mt-0.5" style={{ color: passed ? 'var(--color-teal)' : 'var(--color-rose)' }} />
        <div className="flex-1">
          <div className="text-[13px] font-medium text-[var(--color-ink)] mb-1">
            Empirical time-complexity probe
          </div>
          <p className="text-[12px] text-[var(--color-ink-dim)] leading-relaxed mb-2">{message}</p>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-[11px] font-[var(--font-mono)] px-2 py-1 rounded bg-[var(--color-surface-2)] text-[var(--color-ink)]">
              k ≈ {estimated_exponent}
            </span>
            {samples?.map((s) => (
              <span key={s.n} className="text-[10.5px] font-[var(--font-mono)] text-[var(--color-ink-faint)]">
                n={s.n.toLocaleString()}: {(s.elapsed_seconds * 1000).toFixed(1)}ms
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}
