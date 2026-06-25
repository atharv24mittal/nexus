import { useState, useEffect, useCallback, useRef } from 'react'
import { motion } from 'framer-motion'
import { Play, RotateCcw } from 'lucide-react'
import confetti from 'canvas-confetti'

import Header from './components/Header'
import ProblemSelector from './components/ProblemSelector'
import ModeToggle from './components/ModeToggle'
import LiveSolvePanel from './components/LiveSolvePanel'
import CustomCodePanel from './components/CustomCodePanel'
import SkillLibraryTicker from './components/SkillLibraryTicker'
import InsightsSection from './components/InsightsSection'
import AnimatedBackground from './components/AnimatedBackground'
import SoundToggle from './components/SoundToggle'

import { useProblems, useStats, useCheckCode } from './hooks/useNexus'
import { useSolveStream } from './hooks/useSolveStream'
import { useTheme } from './hooks/useTheme'
import { useSound } from './hooks/useSound'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import { useToast } from './hooks/useToast'
import ToastProvider from './components/ToastProvider'

const STORAGE_KEY = 'nexus:last-session'

function loadSession() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}
  } catch {
    return {}
  }
}

function saveSession(partial) {
  const current = loadSession()
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...current, ...partial }))
}

const DEFAULT_CUSTOM_CODE = `def is_palindrome(s):
    # write your solution here
    return s == s[::-1]
`

function fireConfetti() {
  confetti({
    particleCount: 90,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#FFB454', '#5EEAD4', '#7C9CBF'],
    disableForReducedMotion: true,
  })
}

function AppContent() {
  const session = loadSession()
  const { data: problems, isLoading: problemsLoading } = useProblems()
  const { data: stats, isLoading: statsLoading } = useStats()
  const { theme, toggle: toggleTheme } = useTheme()
  const sound = useSound()
  const toast = useToast()

  const [mode, setMode] = useState(session.mode || 'generate')
  const [selectedProblemId, setSelectedProblemId] = useState(session.problemId || null)
  const [customCode, setCustomCode] = useState(session.customCode || DEFAULT_CUSTOM_CODE)

  // Derived rather than synced-via-effect: once `problems` loads, fall back
  // to the first one if the user (or restored session) hasn't picked yet.
  // Avoids a setState-in-effect render round-trip for what's really just a
  // computed default.
  const problemId = selectedProblemId ?? problems?.[0]?.id ?? null

  const solveStream = useSolveStream()
  const checkMutation = useCheckCode()
  const lastErrorRef = useRef(null)

  useEffect(() => saveSession({ mode }), [mode])
  useEffect(() => saveSession({ problemId }), [problemId])
  useEffect(() => {
    const t = setTimeout(() => saveSession({ customCode }), 400)
    return () => clearTimeout(t)
  }, [customCode])

  // Surface stream-level errors (rate limits, dropped connections) as toasts
  // exactly once each, instead of leaving them silently in panel-only text.
  useEffect(() => {
    if (solveStream.error && solveStream.error !== lastErrorRef.current) {
      lastErrorRef.current = solveStream.error
      toast.push(solveStream.error, 'error')
    }
  }, [solveStream.error, toast])

  useEffect(() => {
    if (checkMutation.error) {
      toast.push(checkMutation.error.message, 'error')
    }
  }, [checkMutation.error, toast])

  const handleSolve = useCallback(() => {
    if (!problemId) return
    solveStream.start(problemId)
  }, [problemId, solveStream])

  const handleCheck = useCallback(() => {
    if (!problemId) return
    checkMutation.mutate({ problemId, code: customCode })
  }, [problemId, customCode, checkMutation])

  const handlePrimaryAction = useCallback(() => {
    if (mode === 'generate') handleSolve()
    else handleCheck()
  }, [mode, handleSolve, handleCheck])

  const handleReset = useCallback(() => {
    solveStream.reset()
    checkMutation.reset()
  }, [solveStream, checkMutation])

  useKeyboardShortcuts({ onSubmit: handlePrimaryAction, onEscape: handleReset })

  useEffect(() => {
    handleReset()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [problemId, mode])

  function handleSolveSuccess() {
    sound.playSuccess()
    fireConfetti()
    toast.push('Solved and formally verified.', 'success', 3000)
  }

  function handleSolveFailure() {
    sound.playFailure()
  }

  return (
    <div className="min-h-screen flex flex-col relative">
      <AnimatedBackground />
      <Header
        llmProvider={stats?.llm_provider}
        llmIsLive={stats?.llm_is_live}
        statsLoading={statsLoading}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      <main className="flex-1 max-w-6xl w-full mx-auto px-5 py-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-6"
        >
          <h1 className="font-[var(--font-display)] text-[26px] font-semibold tracking-tight text-[var(--color-ink)] mb-1.5">
            Generate, execute, verify, repair.
          </h1>
          <p className="text-[13.5px] text-[var(--color-ink-dim)] max-w-2xl">
            NEXUS doesn't trust generated code — it runs it in an isolated sandbox, formally checks
            correctness with property-based tests and a z3 SMT solver, and fixes its own bugs live,
            streamed straight from the server as it happens.
          </p>
        </motion.div>

        <div className="flex flex-wrap items-center gap-3 mb-6">
          <ProblemSelector
            problems={problems}
            selectedId={problemId}
            onSelect={setSelectedProblemId}
            loading={problemsLoading}
          />
          <ModeToggle mode={mode} onChange={setMode} />

          <div className="flex-1" />

          <button
            onClick={handlePrimaryAction}
            disabled={!problemId || solveStream.isStreaming || checkMutation.isPending}
            className="h-11 px-5 rounded-xl bg-[var(--color-amber)] text-[var(--color-bg)] font-medium text-[13.5px] flex items-center gap-2 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
            title="Ctrl/Cmd + Enter"
          >
            <Play size={15} fill="currentColor" />
            {mode === 'generate'
              ? (solveStream.isStreaming ? 'Solving…' : 'Solve')
              : (checkMutation.isPending ? 'Checking…' : 'Run checks')}
          </button>

          {(solveStream.finalResult || checkMutation.data) && (
            <button
              onClick={handleReset}
              className="h-11 px-3 rounded-xl border border-[var(--color-border)] text-[var(--color-ink-dim)] hover:text-[var(--color-ink)] hover:border-[var(--color-border-bright)] transition-colors"
              title="Clear result (Esc)"
            >
              <RotateCcw size={15} />
            </button>
          )}
        </div>

        <div className="mb-5">
          {mode === 'generate' ? (
            <LiveSolvePanel
              key={solveStream.sessionId}
              stream={solveStream}
              problemId={problemId}
              onSuccess={handleSolveSuccess}
              onFailure={handleSolveFailure}
            />
          ) : (
            <CustomCodePanel
              problemId={problemId}
              code={customCode}
              onCodeChange={(v) => setCustomCode(v ?? '')}
              result={checkMutation.data}
              isPending={checkMutation.isPending}
              error={checkMutation.error?.message}
            />
          )}
        </div>

        <InsightsSection />
      </main>

      <footer className="border-t border-[var(--color-border)] py-4">
        <div className="max-w-6xl mx-auto px-5 flex items-center justify-between flex-wrap gap-3">
          <SkillLibraryTicker stats={stats} loading={statsLoading} />
          <div className="flex items-center gap-3">
            <SoundToggle enabled={sound.enabled} onToggle={sound.setEnabled} />
            <div className="text-[11.5px] text-[var(--color-ink-faint)] font-[var(--font-mono)]">
              Built by Atharv Mittal · NEXUS v2.0.0
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  )
}
