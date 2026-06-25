import { motion, AnimatePresence } from 'framer-motion'
import { useState, useRef, useEffect, useMemo } from 'react'
import { ChevronDown, Check, Search } from 'lucide-react'

const DIFFICULTY_COLOR = {
  easy: 'var(--color-teal)',
  medium: 'var(--color-amber)',
  hard: 'var(--color-rose)',
}

const DIFFICULTY_FILTERS = ['all', 'easy', 'medium', 'hard']

export default function ProblemSelector({ problems, selectedId, onSelect, loading }) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [difficultyFilter, setDifficultyFilter] = useState('all')
  const ref = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    function onClickOutside(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  const selected = problems?.find((p) => p.id === selectedId)

  const filtered = useMemo(() => {
    if (!problems) return []
    return problems.filter((p) => {
      const matchesQuery = p.title.toLowerCase().includes(query.toLowerCase()) || p.id.includes(query.toLowerCase())
      const matchesDifficulty = difficultyFilter === 'all' || p.difficulty === difficultyFilter
      return matchesQuery && matchesDifficulty
    })
  }, [problems, query, difficultyFilter])

  if (loading) {
    return <div className="h-11 w-64 rounded-xl shimmer-bg border border-[var(--color-border)]" />
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="h-11 min-w-64 px-3.5 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] hover:border-[var(--color-border-bright)] flex items-center justify-between gap-3 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <span
            className="w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ background: DIFFICULTY_COLOR[selected?.difficulty] || 'var(--color-ink-faint)' }}
          />
          <span className="text-[13.5px] font-medium text-[var(--color-ink)] truncate">
            {selected?.title || 'Select a problem'}
          </span>
        </div>
        <ChevronDown
          size={16}
          className={`text-[var(--color-ink-faint)] transition-transform duration-200 flex-shrink-0 ${open ? 'rotate-180' : ''}`}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute top-full mt-1.5 w-80 rounded-xl bg-[var(--color-surface-2)] border border-[var(--color-border-bright)] shadow-2xl shadow-black/40 overflow-hidden z-40"
          >
            <div className="p-2 border-b border-[var(--color-border)] space-y-2">
              <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[var(--color-surface)] border border-[var(--color-border)]">
                <Search size={13} className="text-[var(--color-ink-faint)] flex-shrink-0" />
                <input
                  ref={inputRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search problems…"
                  className="flex-1 bg-transparent outline-none text-[12.5px] text-[var(--color-ink)] placeholder:text-[var(--color-ink-faint)]"
                />
              </div>
              <div className="flex gap-1">
                {DIFFICULTY_FILTERS.map((d) => (
                  <button
                    key={d}
                    onClick={() => setDifficultyFilter(d)}
                    className="flex-1 text-[10.5px] font-[var(--font-mono)] py-1 rounded-md transition-colors capitalize"
                    style={{
                      background: difficultyFilter === d ? 'var(--color-surface-3)' : 'transparent',
                      color: difficultyFilter === d ? 'var(--color-ink)' : 'var(--color-ink-faint)',
                    }}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            <div className="max-h-72 overflow-y-auto py-1">
              {filtered.length === 0 ? (
                <div className="text-[12px] text-[var(--color-ink-faint)] text-center py-6">No problems match.</div>
              ) : (
                filtered.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => {
                      onSelect(p.id)
                      setOpen(false)
                      setQuery('')
                    }}
                    className="w-full px-3.5 py-2.5 flex items-center justify-between gap-2 hover:bg-[var(--color-surface-3)] transition-colors text-left"
                  >
                    <div className="flex items-center gap-2.5">
                      <span
                        className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ background: DIFFICULTY_COLOR[p.difficulty] }}
                      />
                      <span className="text-[13px] text-[var(--color-ink)]">{p.title}</span>
                    </div>
                    {p.id === selectedId && <Check size={14} className="text-[var(--color-amber)]" />}
                  </button>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
