import { motion } from 'framer-motion'
import { Check, X, Loader2 } from 'lucide-react'

export default function AttemptTimeline({ attempts, currentIndex, onJumpTo, isAnimating, inProgressAttemptNumber }) {
  const showInProgressMarker = isAnimating && inProgressAttemptNumber && inProgressAttemptNumber > attempts.length
  if ((!attempts || attempts.length === 0) && !showInProgressMarker) return null

  return (
    <div className="flex items-center gap-2 overflow-x-auto pb-1">
      {attempts.map((attempt, i) => {
        const isCurrent = i === currentIndex
        const isRevealed = i <= currentIndex

        return (
          <div key={attempt.attempt_number} className="flex items-center gap-2 flex-shrink-0">
            {i > 0 && (
              <div
                className="w-5 h-px"
                style={{ background: isRevealed ? 'var(--color-border-bright)' : 'var(--color-border)' }}
              />
            )}
            <motion.button
              onClick={() => isRevealed && onJumpTo(i)}
              disabled={!isRevealed}
              whileHover={isRevealed ? { scale: 1.05 } : {}}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11.5px] font-[var(--font-mono)] transition-colors disabled:cursor-default"
              style={{
                borderColor: isCurrent ? 'var(--color-amber)' : isRevealed ? 'var(--color-border-bright)' : 'var(--color-border)',
                background: isCurrent ? 'rgba(255,180,84,0.08)' : 'var(--color-surface)',
                color: isRevealed ? 'var(--color-ink)' : 'var(--color-ink-faint)',
                opacity: isRevealed ? 1 : 0.5,
              }}
            >
              <span>{String(attempt.attempt_number).padStart(2, '0')}</span>
              {attempt.verification_passed ? (
                <Check size={11} className="text-[var(--color-teal)]" />
              ) : (
                <X size={11} className="text-[var(--color-rose)]" />
              )}
            </motion.button>
          </div>
        )
      })}
      {showInProgressMarker && (
        <div className="flex items-center gap-2 flex-shrink-0">
          {attempts.length > 0 && <div className="w-5 h-px" style={{ background: 'var(--color-border-bright)' }} />}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11.5px] font-[var(--font-mono)]"
            style={{ borderColor: 'var(--color-amber)', background: 'rgba(255,180,84,0.08)', color: 'var(--color-ink)' }}
          >
            <span>{String(inProgressAttemptNumber).padStart(2, '0')}</span>
            <Loader2 size={11} className="animate-spin text-[var(--color-amber)]" />
          </motion.div>
        </div>
      )}
    </div>
  )
}
