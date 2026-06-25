import { useState } from 'react'
import { Link2, Check } from 'lucide-react'

export default function ShareButton({ resultId }) {
  const [copied, setCopied] = useState(false)
  if (!resultId) return null

  async function handleClick() {
    const url = `${window.location.origin}${window.location.pathname}#/result/${resultId}`
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    } catch {
      /* clipboard API unavailable - silently no-op rather than throw */
    }
  }

  return (
    <button
      onClick={handleClick}
      className="flex items-center gap-1.5 text-[11.5px] px-2.5 py-1.5 rounded-lg border border-[var(--color-border)] text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] hover:border-[var(--color-border-bright)] transition-colors"
      title="Copy a shareable link to this result"
    >
      {copied ? <Check size={12} className="text-[var(--color-teal)]" /> : <Link2 size={12} />}
      {copied ? 'Copied!' : 'Share'}
    </button>
  )
}
