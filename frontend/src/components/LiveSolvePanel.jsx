import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import CodeEditor from './CodeEditor'
import PhaseIndicator from './PhaseIndicator'
import TraceBeam from './TraceBeam'
import VerificationCard from './VerificationCard'
import ComplexityCard from './ComplexityCard'
import AttemptTimeline from './AttemptTimeline'
import DiffViewer from './DiffViewer'
import TestCaseExplorer from './TestCaseExplorer'
import ExplainHintPanel from './ExplainHintPanel'
import ShareButton from './ShareButton'
import CodeActions from './CodeActions'
import { GitCompare } from 'lucide-react'

export default function LiveSolvePanel({ stream, problemId, onSuccess, onFailure }) {
  const { isStreaming, phase, attempts, attemptNumber, currentCode, currentTrace,
          currentStdout, currentVerification, currentComplexity, finalResult, error } = stream

  // null = "pinned to latest" (follows the in-progress attempt while
  // streaming); any number = the user explicitly jumped to that attempt via
  // the timeline. Derived rather than synced via an effect — and since
  // App.jsx remounts this component fresh (via `key={sessionId}`) for every
  // new solve, this naturally resets to "pinned" with no extra code.
  const [manualViewIndex, setManualViewIndex] = useState(null)
  const [showDiff, setShowDiff] = useState(false)
  const notifiedRef = useRef(false)

  const viewIndex = manualViewIndex ?? attempts.length

  useEffect(() => {
    if (finalResult && !notifiedRef.current) {
      notifiedRef.current = true
      if (finalResult.success) onSuccess?.(finalResult)
      else onFailure?.(finalResult)
    }
    if (!finalResult) notifiedRef.current = false
  }, [finalResult, onSuccess, onFailure])

  if (!isStreaming && attempts.length === 0 && !finalResult) {
    return (
      <div className="rounded-2xl border border-dashed border-[var(--color-border)] bg-[var(--color-surface)]/40 h-[420px] flex flex-col items-center justify-center gap-2 text-center px-8">
        <div className="text-[14px] text-[var(--color-ink-dim)]">Pick a problem and hit Solve</div>
        <div className="text-[12px] text-[var(--color-ink-faint)] max-w-sm">
          NEXUS streams every real step live — generation, sandbox execution, verification, and
          repair — straight from the server as it happens.
        </div>
      </div>
    )
  }

  const completedAttempt = attempts[viewIndex]
  const isViewingInProgress = viewIndex >= attempts.length
  const displayedCode = isViewingInProgress ? currentCode : completedAttempt?.code
  const displayedTrace = isViewingInProgress ? currentTrace : completedAttempt?.trace
  const displayedStdout = isViewingInProgress ? currentStdout : completedAttempt?.stdout
  const displayedVerification = isViewingInProgress
    ? currentVerification
    : completedAttempt && {
        passed: completedAttempt.verification_passed,
        message: completedAttempt.verification_message,
        method: completedAttempt.verification_method,
        violated_constraint: completedAttempt.violated_constraint,
        counterexample: completedAttempt.counterexample,
      }
  const displayedComplexity = isViewingInProgress ? currentComplexity : completedAttempt?.complexity_check

  const previousAttempt = viewIndex > 0 ? attempts[viewIndex - 1] : null

  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <div className="px-4 py-3 border-b border-[var(--color-border)] flex items-center justify-between gap-3">
        <PhaseIndicator phase={phase} success={finalResult?.success} />
        <div className="flex items-center gap-2">
          {finalResult && <ShareButton resultId={finalResult.result_id} />}
          {displayedCode && <CodeActions code={displayedCode} filename={`${problemId}_attempt_${(completedAttempt?.attempt_number ?? attemptNumber)}.py`} />}
        </div>
      </div>

      {error && (
        <div className="px-4 py-3 text-[12.5px] text-[var(--color-rose)] font-[var(--font-mono)] border-b border-[var(--color-border)]">
          {error}
        </div>
      )}

      <div className="px-4 py-2.5 border-b border-[var(--color-border)] flex items-center justify-between gap-2">
        <AttemptTimeline
          attempts={attempts}
          currentIndex={viewIndex}
          onJumpTo={setManualViewIndex}
          isAnimating={isStreaming}
          inProgressAttemptNumber={attemptNumber}
        />
        {previousAttempt && (
          <button
            onClick={() => setShowDiff((s) => !s)}
            className="flex items-center gap-1.5 text-[11px] text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] flex-shrink-0 transition-colors"
          >
            <GitCompare size={12} /> {showDiff ? 'Hide diff' : 'Diff vs previous'}
          </button>
        )}
      </div>

      {showDiff && previousAttempt && (
        <div className="px-4 py-3 border-b border-[var(--color-border)] max-h-48 overflow-y-auto">
          <DiffViewer before={previousAttempt.code} after={displayedCode} />
        </div>
      )}

      <div className="grid md:grid-cols-2">
        <div className="h-[300px] border-b md:border-b-0 md:border-r border-[var(--color-border)]">
          <AnimatePresence mode="wait">
            <motion.div key={viewIndex} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }} className="h-full">
              <CodeEditor value={displayedCode || ''} readOnly />
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="h-[300px] overflow-y-auto bg-[var(--color-surface-2)]/50">
          <AnimatePresence mode="wait">
            {phase === 'retrieving' && isViewingInProgress ? (
              <motion.div key="retrieving" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex items-center justify-center text-center px-6">
                <div className="text-[12.5px] text-[var(--color-ink-dim)] font-[var(--font-mono)]">
                  Searching memory for similar past fixes…
                </div>
              </motion.div>
            ) : (
              <motion.div key={`trace-${viewIndex}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <TraceBeam trace={displayedTrace} active={phase === 'executing'} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      <div className="p-4 space-y-3">
        {displayedVerification && <VerificationCard attempt={{
          verification_passed: displayedVerification.passed,
          verification_message: displayedVerification.message,
          verification_method: displayedVerification.method,
          violated_constraint: displayedVerification.violated_constraint,
          counterexample: displayedVerification.counterexample,
        }} />}
        {displayedComplexity && <ComplexityCard complexityCheck={displayedComplexity} />}

        <TestCaseExplorer stdout={displayedStdout} trace={displayedTrace} />

        {!isStreaming && displayedCode && (
          <ExplainHintPanel problemId={problemId} code={displayedCode} mode="generate" />
        )}

        {finalResult && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center justify-between text-[11.5px] text-[var(--color-ink-faint)] font-[var(--font-mono)] pt-1">
            <span>
              {attempts.length} attempt{attempts.length === 1 ? '' : 's'} · {finalResult.elapsed_seconds.toFixed(1)}s total · reward {finalResult.reward.toFixed(2)}
            </span>
            <span>{finalResult.llm_provider}</span>
          </motion.div>
        )}
      </div>
    </div>
  )
}
