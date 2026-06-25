import { motion, AnimatePresence } from 'framer-motion'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle({ theme, onToggle }) {
  return (
    <button
      onClick={onToggle}
      aria-label="Toggle light/dark theme"
      className="w-9 h-9 rounded-lg flex items-center justify-center border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-border-bright)] transition-colors overflow-hidden"
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={theme}
          initial={{ rotate: -90, opacity: 0 }}
          animate={{ rotate: 0, opacity: 1 }}
          exit={{ rotate: 90, opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {theme === 'dark' ? (
            <Moon size={15} className="text-[var(--color-dusty)]" />
          ) : (
            <Sun size={15} className="text-[var(--color-amber)]" />
          )}
        </motion.div>
      </AnimatePresence>
    </button>
  )
}
