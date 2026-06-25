import { motion } from 'framer-motion'

/**
 * A small, dependency-free line-level diff: longest-common-subsequence
 * based, good enough for short function bodies (which is all this ever
 * compares). Not meant to replace a real diff library for large files —
 * appropriately scoped for "show what changed between two ~20-line
 * repair attempts."
 */
function diffLines(a, b) {
  const linesA = a.split('\n')
  const linesB = b.split('\n')
  const m = linesA.length, n = linesB.length
  const lcs = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0))

  for (let i = m - 1; i >= 0; i--) {
    for (let j = n - 1; j >= 0; j--) {
      lcs[i][j] = linesA[i] === linesB[j] ? lcs[i + 1][j + 1] + 1 : Math.max(lcs[i + 1][j], lcs[i][j + 1])
    }
  }

  const result = []
  let i = 0, j = 0
  while (i < m && j < n) {
    if (linesA[i] === linesB[j]) {
      result.push({ type: 'same', text: linesA[i] })
      i++; j++
    } else if (lcs[i + 1][j] >= lcs[i][j + 1]) {
      result.push({ type: 'removed', text: linesA[i] })
      i++
    } else {
      result.push({ type: 'added', text: linesB[j] })
      j++
    }
  }
  while (i < m) { result.push({ type: 'removed', text: linesA[i] }); i++ }
  while (j < n) { result.push({ type: 'added', text: linesB[j] }); j++ }
  return result
}

export default function DiffViewer({ before, after }) {
  if (!before || !after) return null
  const lines = diffLines(before, after)
  const hasChanges = lines.some((l) => l.type !== 'same')

  if (!hasChanges) {
    return (
      <div className="text-[12px] text-[var(--color-ink-faint)] font-[var(--font-mono)] px-3 py-3">
        No textual changes between these two attempts.
      </div>
    )
  }

  return (
    <div className="font-[var(--font-mono)] text-[11.5px] rounded-lg overflow-hidden border border-[var(--color-border)]">
      {lines.map((line, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: i * 0.012 }}
          className="px-3 py-0.5 whitespace-pre-wrap break-all"
          style={{
            background:
              line.type === 'added' ? 'rgba(94,234,212,0.10)' :
              line.type === 'removed' ? 'rgba(251,113,133,0.10)' : 'transparent',
            color:
              line.type === 'added' ? 'var(--color-teal)' :
              line.type === 'removed' ? 'var(--color-rose)' : 'var(--color-ink-dim)',
          }}
        >
          <span className="select-none opacity-60 mr-2">
            {line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' '}
          </span>
          {line.text || ' '}
        </motion.div>
      ))}
    </div>
  )
}
