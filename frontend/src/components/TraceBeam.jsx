import { motion } from 'framer-motion'

/**
 * Renders the real execution trace returned by the sandbox (line number +
 * captured local variables at each step) as a vertically-stacked, animated
 * sequence — each step lighting up in turn, like a debugger stepping
 * through the program. All line/variable data is the genuine trace from
 * sys.settrace inside the sandbox, not a simulation.
 */
export default function TraceBeam({ trace, active }) {
  if (!trace || trace.length === 0) {
    return (
      <div className="text-[12px] text-[var(--color-ink-faint)] font-[var(--font-mono)] px-3 py-4">
        No trace captured for this attempt (sandbox error before execution).
      </div>
    )
  }

  const visibleSteps = trace.slice(0, 14) // cap for legibility; same cap as the sandbox's MAX_STEPS

  return (
    <div className="relative px-3 py-2 max-h-64 overflow-y-auto">
      <div
        className="absolute left-[18px] top-2 bottom-2 w-px"
        style={{ background: 'linear-gradient(to bottom, transparent, var(--color-border-bright), transparent)' }}
      />
      <div className="space-y-1">
        {visibleSteps.map((step, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: active ? i * 0.045 : 0, duration: 0.2 }}
            className="relative flex items-start gap-2.5 py-1 pl-7"
          >
            <span
              className="absolute left-[14px] top-1.5 w-2 h-2 rounded-full border-2"
              style={{ borderColor: 'var(--color-amber)', background: 'var(--color-bg)' }}
            />
            <span className="text-[11px] font-[var(--font-mono)] text-[var(--color-ink-faint)] w-9 flex-shrink-0 pt-0.5">
              L{step.line}
            </span>
            <div className="flex flex-wrap gap-x-2.5 gap-y-0.5 text-[11px] font-[var(--font-mono)]">
              {Object.entries(step.locals).length === 0 ? (
                <span className="text-[var(--color-ink-faint)] italic">no locals yet</span>
              ) : (
                Object.entries(step.locals).map(([k, v]) => (
                  <span key={k}>
                    <span className="text-[var(--color-dusty)]">{k}</span>
                    <span className="text-[var(--color-ink-faint)]">=</span>
                    <span className="text-[var(--color-ink-dim)]">{v}</span>
                  </span>
                ))
              )}
            </div>
          </motion.div>
        ))}
      </div>
      {trace.length > visibleSteps.length && (
        <div className="text-[10.5px] text-[var(--color-ink-faint)] font-[var(--font-mono)] pl-7 pt-1">
          …{trace.length - visibleSteps.length} more steps captured (truncated for display)
        </div>
      )}
    </div>
  )
}
