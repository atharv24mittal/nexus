import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, Lightbulb, Loader2 } from 'lucide-react'
import { useExplain, useHint } from '../hooks/useNexus'

export default function ExplainHintPanel({ problemId, code, errorMessage, mode }) {
  const [result, setResult] = useState(null)
  const explainMutation = useExplain()
  const hintMutation = useHint()

  const isPending = explainMutation.isPending || hintMutation.isPending

  function handleExplain() {
    setResult(null)
    explainMutation.mutate({ problemId, code }, {
      onSuccess: (data) => setResult({ kind: 'explanation', text: data.explanation, cached: data.cached }),
    })
  }

  function handleHint() {
    setResult(null)
    hintMutation.mutate({ problemId, code, errorMessage }, {
      onSuccess: (data) => setResult({ kind: 'hint', text: data.hint, cached: data.cached }),
    })
  }

  return (
    <div className="space-y-2.5">
      <div className="flex gap-2">
        <button
          onClick={handleExplain}
          disabled={isPending || !code}
          className="flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-lg border border-[var(--color-border)] text-[var(--color-ink-dim)] hover:text-[var(--color-ink)] hover:border-[var(--color-border-bright)] disabled:opacity-40 transition-colors"
        >
          <Sparkles size={13} /> Explain this solution
        </button>
        {mode === 'custom' && (
          <button
            onClick={handleHint}
            disabled={isPending || !code}
            className="flex items-center gap-1.5 text-[12px] px-3 py-1.5 rounded-lg border border-[var(--color-border)] text-[var(--color-ink-dim)] hover:text-[var(--color-ink)] hover:border-[var(--color-border-bright)] disabled:opacity-40 transition-colors"
          >
            <Lightbulb size={13} /> Get a hint
          </button>
        )}
        {isPending && <Loader2 size={14} className="animate-spin text-[var(--color-amber)] self-center" />}
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="rounded-xl border border-[var(--color-border)] p-3.5"
            style={{ background: result.kind === 'hint' ? 'rgba(255,180,84,0.06)' : 'var(--color-surface-2)' }}
          >
            <div className="flex items-center gap-2 mb-1.5">
              {result.kind === 'hint' ? (
                <Lightbulb size={14} className="text-[var(--color-amber)]" />
              ) : (
                <Sparkles size={14} className="text-[var(--color-dusty)]" />
              )}
              <span className="text-[11.5px] font-medium text-[var(--color-ink)]">
                {result.kind === 'hint' ? 'Hint' : 'Explanation'}
              </span>
              {result.cached && (
                <span className="text-[10px] font-[var(--font-mono)] text-[var(--color-ink-faint)]">cached</span>
              )}
            </div>
            <p className="text-[12.5px] text-[var(--color-ink-dim)] leading-relaxed">{result.text}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
