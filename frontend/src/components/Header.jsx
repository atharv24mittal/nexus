import { motion } from 'framer-motion'
import ThemeToggle from './ThemeToggle'

function GithubMark({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.08 3.29 9.39 7.86 10.9.57.1.78-.25.78-.55 0-.27-.01-1.17-.02-2.12-3.2.7-3.87-1.36-3.87-1.36-.53-1.32-1.28-1.67-1.28-1.67-1.05-.71.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.75 2.7 1.25 3.36.95.1-.75.4-1.25.72-1.54-2.55-.29-5.24-1.28-5.24-5.7 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11 11 0 0 1 5.79 0c2.21-1.49 3.18-1.18 3.18-1.18.62 1.59.23 2.76.11 3.05.74.81 1.18 1.84 1.18 3.1 0 4.43-2.7 5.41-5.27 5.69.42.36.78 1.07.78 2.16 0 1.56-.01 2.81-.01 3.2 0 .31.21.66.79.55A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5z" />
    </svg>
  )
}

function TraceMark() {
  return (
    <svg viewBox="0 0 32 32" className="w-5 h-5">
      <path
        d="M6 22 L12 22 L15 10 L18 24 L21 16 L26 16"
        stroke="var(--color-amber)"
        strokeWidth="2.4"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default function Header({ llmProvider, llmIsLive, statsLoading, theme, onToggleTheme }) {
  return (
    <header className="border-b border-[var(--color-border)] bg-[var(--color-bg)]/95 backdrop-blur sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-5 py-3.5 flex items-center justify-between gap-4">
        <motion.div
          className="flex items-center gap-2.5"
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="w-8 h-8 rounded-[9px] bg-[var(--color-surface)] border border-[var(--color-border)] flex items-center justify-center">
            <TraceMark />
          </div>
          <div className="leading-tight">
            <div className="font-[var(--font-display)] font-semibold text-[15px] tracking-tight text-[var(--color-ink)]">
              NEXUS
            </div>
            <div className="text-[10.5px] text-[var(--color-ink-faint)] -mt-0.5">
              execution-aware code intelligence
            </div>
          </div>
        </motion.div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                statsLoading
                  ? 'bg-[var(--color-ink-faint)]'
                  : llmIsLive
                  ? 'bg-[var(--color-teal)]'
                  : 'bg-[var(--color-rose)]'
              }`}
              style={!statsLoading && llmIsLive ? { animation: 'pulse-dot 2s ease-in-out infinite' } : undefined}
            />
            <span className="text-[11.5px] font-[var(--font-mono)] text-[var(--color-ink-dim)]">
              {statsLoading ? 'connecting…' : llmIsLive ? llmProvider : 'offline mode'}
            </span>
          </div>

          <a
            href="https://github.com/atharv24mittal/nexus"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[var(--color-ink-dim)] hover:text-[var(--color-ink)] hover:bg-[var(--color-surface)] transition-colors text-[12.5px]"
          >
            <GithubMark size={15} />
            <span className="hidden sm:inline">Source</span>
          </a>

          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </div>
    </header>
  )
}
