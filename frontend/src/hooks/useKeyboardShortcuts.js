import { useEffect } from 'react'

/**
 * Binds Ctrl/Cmd+Enter to `onSubmit` and Escape to `onEscape`, globally.
 * Skips firing while focus is in a context where Enter should do something
 * else entirely (handled naturally since Monaco/inputs stop propagation
 * for their own Enter handling; this listens at the window level for the
 * *modified* Enter combination specifically, which nothing else claims).
 */
export function useKeyboardShortcuts({ onSubmit, onEscape }) {
  useEffect(() => {
    function handler(e) {
      const isSubmitCombo = (e.metaKey || e.ctrlKey) && e.key === 'Enter'
      if (isSubmitCombo && onSubmit) {
        e.preventDefault()
        onSubmit()
      } else if (e.key === 'Escape' && onEscape) {
        onEscape()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onSubmit, onEscape])
}
