import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Terminal } from 'lucide-react'

export default function TestCaseExplorer({ stdout, trace }) {
  const [open, setOpen] = useState(false)
  const hasContent = Boolean(stdout) || (trace && trace.length > 0)

  if (!hasContent) return null

  return (
    <div className="rounded-xl border border-[var(--color-border)] overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-3.5 py-2.5 hover:bg-[var(--color-surface-2)] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Terminal size={13} className="text-[var(--color-dusty)]" />
          <span className="text-[12px] text-[var(--color-ink-dim)] font-[var(--font-mono)]">
            Sandbox stdout {stdout ? `(${stdout.split('\n').length} lines)` : '(empty)'}
          </span>
        </div>
        <ChevronDown size={14} className={`text-[var(--color-ink-faint)] transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <pre className="px-3.5 py-3 text-[11px] font-[var(--font-mono)] text-[var(--color-ink-dim)] bg-[var(--color-bg)] max-h-40 overflow-y-auto whitespace-pre-wrap">
              {stdout || '(this candidate printed nothing to stdout)'}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
