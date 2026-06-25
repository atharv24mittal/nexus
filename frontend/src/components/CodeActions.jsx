import { useState } from 'react'
import { Copy, Check, Download } from 'lucide-react'

export default function CodeActions({ code, filename = 'solution.py' }) {
  const [copied, setCopied] = useState(false)
  if (!code) return null

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1600)
    } catch {
      /* clipboard API unavailable - silently no-op */
    }
  }

  function handleDownload() {
    const blob = new Blob([code], { type: 'text/x-python' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex gap-1.5">
      <button
        onClick={handleCopy}
        className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-md border border-[var(--color-border)] text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] transition-colors"
        title="Copy code"
      >
        {copied ? <Check size={11} className="text-[var(--color-teal)]" /> : <Copy size={11} />}
      </button>
      <button
        onClick={handleDownload}
        className="flex items-center gap-1 text-[11px] px-2 py-1 rounded-md border border-[var(--color-border)] text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] transition-colors"
        title="Download as .py"
      >
        <Download size={11} />
      </button>
    </div>
  )
}
