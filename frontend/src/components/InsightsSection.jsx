import { useState, Suspense, lazy } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, History, BarChart3 } from 'lucide-react'

const HistoryPanel = lazy(() => import('./HistoryPanel'))
const StatsDashboard = lazy(() => import('./StatsDashboard'))

function PanelSkeleton() {
  return (
    <div className="space-y-2">
      {[1, 2, 3].map((i) => <div key={i} className="h-10 rounded-lg shimmer-bg" />)}
    </div>
  )
}

export default function InsightsSection() {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState('history')

  return (
    <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-[var(--color-surface-2)] transition-colors"
      >
        <span className="text-[12.5px] font-medium text-[var(--color-ink-dim)]">
          History &amp; stats
        </span>
        <ChevronDown size={15} className={`text-[var(--color-ink-faint)] transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <div className="border-t border-[var(--color-border)] p-4">
              <div className="flex gap-1 mb-4 p-1 rounded-lg bg-[var(--color-surface-2)] w-fit">
                <button
                  onClick={() => setTab('history')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] transition-colors"
                  style={{
                    background: tab === 'history' ? 'var(--color-surface-3)' : 'transparent',
                    color: tab === 'history' ? 'var(--color-ink)' : 'var(--color-ink-faint)',
                  }}
                >
                  <History size={13} /> Recent solves
                </button>
                <button
                  onClick={() => setTab('stats')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[12px] transition-colors"
                  style={{
                    background: tab === 'stats' ? 'var(--color-surface-3)' : 'transparent',
                    color: tab === 'stats' ? 'var(--color-ink)' : 'var(--color-ink-faint)',
                  }}
                >
                  <BarChart3 size={13} /> Aggregate stats
                </button>
              </div>

              <Suspense fallback={<PanelSkeleton />}>
                {tab === 'history' ? <HistoryPanel /> : <StatsDashboard />}
              </Suspense>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
