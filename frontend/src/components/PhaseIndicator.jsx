import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Cpu, ShieldCheck, CheckCircle2, XCircle, BookOpen } from 'lucide-react'

const PHASE_CONFIG = {
  idle: { label: 'Ready', icon: Sparkles, color: 'var(--color-ink-faint)' },
  generating: { label: 'Generating candidate code…', icon: Sparkles, color: 'var(--color-amber)' },
  executing: { label: 'Executing in sandbox…', icon: Cpu, color: 'var(--color-dusty)' },
  verifying: { label: 'Verifying correctness…', icon: ShieldCheck, color: 'var(--color-teal)' },
  retrieving: { label: 'Retrieving similar past fixes…', icon: BookOpen, color: 'var(--color-amber)' },
  done: { label: 'Done', icon: CheckCircle2, color: 'var(--color-teal)' },
}

export default function PhaseIndicator({ phase, success }) {
  const cfg = PHASE_CONFIG[phase] || PHASE_CONFIG.idle
  const Icon = phase === 'done' ? (success ? CheckCircle2 : XCircle) : cfg.icon
  const color = phase === 'done' ? (success ? 'var(--color-teal)' : 'var(--color-rose)') : cfg.color

  return (
    <div className="flex items-center gap-2.5 h-7">
      <AnimatePresence mode="wait">
        <motion.div
          key={phase}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.18 }}
          className="flex items-center gap-2"
        >
          <motion.div
            animate={phase !== 'idle' && phase !== 'done' ? { scale: [1, 1.15, 1] } : { scale: 1 }}
            transition={{ duration: 1.1, repeat: phase !== 'idle' && phase !== 'done' ? Infinity : 0, ease: 'easeInOut' }}
          >
            <Icon size={15} style={{ color }} />
          </motion.div>
          <span className="text-[12.5px] font-[var(--font-mono)]" style={{ color }}>
            {phase === 'done' ? (success ? 'Verified correct' : 'Failed all repair attempts') : cfg.label}
          </span>
        </motion.div>
      </AnimatePresence>
      {phase !== 'idle' && phase !== 'done' && (
        <span className="flex gap-0.5">
          {[0, 1, 2].map((i) => (
            <span
              key={i}
              className="w-1 h-1 rounded-full"
              style={{ background: color, animation: `pulse-dot 1.2s ease-in-out ${i * 0.15}s infinite` }}
            />
          ))}
        </span>
      )}
    </div>
  )
}
