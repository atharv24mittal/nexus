import { motion } from 'framer-motion'
import { CheckCircle2, XCircle } from 'lucide-react'
import CodeEditor from './CodeEditor'
import ComplexityCard from './ComplexityCard'
import ExplainHintPanel from './ExplainHintPanel'
import CodeActions from './CodeActions'
import TestCaseExplorer from './TestCaseExplorer'

export default function CustomCodePanel({ problemId, code, onCodeChange, result, isPending, error }) {
  const firstFailure = result?.checks?.find((c) => !c.passed)

  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between gap-3">
        <span className="text-[12.5px] text-[var(--color-ink-dim)] font-[var(--font-mono)]">
          Paste your own solution — runs through the exact same sandbox + verifier, no AI involved.
        </span>
        <CodeActions code={code} filename={`${problemId}_custom.py`} />
      </div>

      <div className="grid md:grid-cols-2">
        <div className="h-[300px] border-b md:border-b-0 md:border-r border-[var(--color-border)]">
          <CodeEditor value={code} onChange={onCodeChange} />
        </div>

        <div className="h-[300px] overflow-y-auto p-4">
          {isPending && (
            <div className="space-y-2.5">
              {[90, 70, 85].map((w, i) => (
                <div key={i} className="h-3 rounded shimmer-bg" style={{ width: `${w}%` }} />
              ))}
            </div>
          )}

          {error && (
            <div className="text-[12.5px] text-[var(--color-rose)] font-[var(--font-mono)]">{error}</div>
          )}

          {!isPending && !error && !result && (
            <div className="text-[12.5px] text-[var(--color-ink-faint)] h-full flex items-center justify-center text-center">
              Click "Run checks" to verify your code against 10 randomized test cases.
            </div>
          )}

          {result && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2.5">
              <div className="flex items-center gap-2 mb-2">
                {result.passed ? (
                  <CheckCircle2 size={16} className="text-[var(--color-teal)]" />
                ) : (
                  <XCircle size={16} className="text-[var(--color-rose)]" />
                )}
                <span className="text-[13px] font-medium text-[var(--color-ink)]">
                  {result.passed ? 'All checks passed' : 'Some checks failed'}
                </span>
                <span className="text-[11px] font-[var(--font-mono)] text-[var(--color-ink-faint)]">
                  {result.checks.filter((c) => c.passed).length}/{result.checks.length} cases
                </span>
              </div>

              {result.checks
                .filter((c) => !c.passed)
                .slice(0, 3)
                .map((c, i) => (
                  <div
                    key={i}
                    className="text-[11.5px] font-[var(--font-mono)] rounded-lg p-2.5 bg-[rgba(251,113,133,0.06)] border border-[var(--color-rose-dim)] text-[var(--color-ink-dim)]"
                  >
                    <div className="text-[var(--color-rose)] mb-1">{c.message}</div>
                    <div className="text-[var(--color-ink-faint)]">input: {JSON.stringify(c.input)}</div>
                  </div>
                ))}

              {result.complexity_check && <ComplexityCard complexityCheck={result.complexity_check} />}
              <TestCaseExplorer stdout={result.stdout} trace={result.trace} />
            </motion.div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-[var(--color-border)]">
        <ExplainHintPanel
          problemId={problemId}
          code={code}
          errorMessage={firstFailure?.message}
          mode="custom"
        />
      </div>
    </div>
  )
}
