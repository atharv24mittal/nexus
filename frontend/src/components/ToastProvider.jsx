import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from 'lucide-react'
import { ToastContext } from '../lib/toastContext'

const ICONS = { success: CheckCircle2, error: XCircle, info: Info, warning: AlertTriangle }
const COLORS = {
  success: 'var(--color-teal)',
  error: 'var(--color-rose)',
  info: 'var(--color-dusty)',
  warning: 'var(--color-amber)',
}

let nextId = 1

export default function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const push = useCallback((message, type = 'info', duration = 4000) => {
    const id = nextId++
    setToasts((prev) => [...prev, { id, message, type }])
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration)
    }
    return id
  }, [dismiss])

  return (
    <ToastContext.Provider value={{ push, dismiss }}>
      {children}
      <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm">
        <AnimatePresence>
          {toasts.map((t) => {
            const Icon = ICONS[t.type] || Info
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 12, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: 40, scale: 0.96 }}
                transition={{ duration: 0.2 }}
                className="flex items-start gap-2.5 px-3.5 py-3 rounded-xl border shadow-lg shadow-black/20"
                style={{
                  background: 'var(--color-surface-2)',
                  borderColor: 'var(--color-border-bright)',
                }}
              >
                <Icon size={16} style={{ color: COLORS[t.type], flexShrink: 0, marginTop: 1 }} />
                <span className="text-[12.5px] text-[var(--color-ink)] leading-snug flex-1">{t.message}</span>
                <button
                  onClick={() => dismiss(t.id)}
                  className="text-[var(--color-ink-faint)] hover:text-[var(--color-ink)] flex-shrink-0"
                >
                  <X size={13} />
                </button>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  )
}
