import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, FunctionSquare, Sigma, FlaskConical } from 'lucide-react'

const METHOD_META = {
  property_based: { label: 'Property-based check', icon: FlaskConical, color: 'var(--color-dusty)' },
  smt_z3: { label: 'z3 SMT proof', icon: Sigma, color: 'var(--color-amber)' },
  ground_truth: { label: 'Ground-truth comparison', icon: FunctionSquare, color: 'var(--color-dusty)' },
  empirical_complexity_probe: { label: 'Empirical complexity probe', icon: Sigma, color: 'var(--color-amber)' },
  sandbox: { label: 'Sandbox execution', icon: FlaskConical, color: 'var(--color-rose)' },
}

export default function VerificationCard({ attempt }) {
  if (!attempt) return null
  const passed = attempt.verification_passed
  const meta = METHOD_META[attempt.verification_method] || METHOD_META.property_based
  const Icon = meta.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="rounded-xl border p-3.5"
      style={{
        borderColor: passed ? 'var(--color-teal-dim)' : 'var(--color-rose-dim)',
        background: passed ? 'rgba(94,234,212,0.06)' : 'rgba(251,113,133,0.06)',
      }}
    >
      <div className="flex items-start gap-2.5">
        {passed ? (
          <CheckCircle2 size={17} className="text-[var(--color-teal)] flex-shrink-0 mt-0.5" />
        ) : (
          <XCircle size={17} className="text-[var(--color-rose)] flex-shrink-0 mt-0.5" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[13px] font-medium text-[var(--color-ink)]">
              {passed ? 'All checks passed' : 'Constraint violated'}
            </span>
            <span
              className="flex items-center gap-1 text-[10.5px] font-[var(--font-mono)] px-1.5 py-0.5 rounded"
              style={{ color: meta.color, background: 'var(--color-surface-2)' }}
            >
              <Icon size={10} />
              {meta.label}
            </span>
          </div>
          <p className="text-[12px] text-[var(--color-ink-dim)] leading-relaxed">{attempt.verification_message}</p>
          {attempt.violated_constraint && !passed && (
            <div className="mt-2 text-[11px] font-[var(--font-mono)] text-[var(--color-rose)] bg-[var(--color-surface-2)] rounded px-2 py-1 inline-block">
              violated: {attempt.violated_constraint}
            </div>
          )}
          {attempt.counterexample && (
            <details className="mt-2">
              <summary className="text-[11px] text-[var(--color-ink-faint)] cursor-pointer hover:text-[var(--color-ink-dim)]">
                Counterexample
              </summary>
              <pre className="text-[10.5px] font-[var(--font-mono)] text-[var(--color-ink-dim)] mt-1.5 bg-[var(--color-surface-2)] rounded p-2 overflow-x-auto">
                {JSON.stringify(attempt.counterexample, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    </motion.div>
  )
}
