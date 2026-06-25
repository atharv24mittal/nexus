import { Volume2, VolumeX } from 'lucide-react'

export default function SoundToggle({ enabled, onToggle }) {
  return (
    <button
      onClick={() => onToggle(!enabled)}
      aria-label="Toggle sound effects"
      title={enabled ? 'Sound effects on' : 'Sound effects off'}
      className="flex items-center gap-1.5 text-[11.5px] text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] transition-colors"
    >
      {enabled ? <Volume2 size={13} /> : <VolumeX size={13} />}
    </button>
  )
}
