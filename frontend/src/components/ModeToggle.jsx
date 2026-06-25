import { motion } from 'framer-motion'

export default function ModeToggle({ mode, onChange }) {
  const options = [
    { id: 'generate', label: 'NEXUS generates' },
    { id: 'custom', label: 'Test my code' },
  ]
  return (
    <div className="relative inline-flex h-11 p-1 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
      {options.map((opt) => {
        const active = mode === opt.id
        return (
          <button
            key={opt.id}
            onClick={() => onChange(opt.id)}
            className="relative px-4 text-[12.5px] font-medium rounded-lg z-10 transition-colors"
            style={{ color: active ? 'var(--color-bg)' : 'var(--color-ink-dim)' }}
          >
            {active && (
              <motion.div
                layoutId="mode-pill"
                className="absolute inset-0 rounded-lg bg-[var(--color-amber)] -z-10"
                transition={{ type: 'spring', stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative">{opt.label}</span>
          </button>
        )
      })}
    </div>
  )
}
