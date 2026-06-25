import { useState, useCallback, useRef, useEffect } from 'react'

const STORAGE_KEY = 'nexus:sound-enabled'

/**
 * Tiny beep effects synthesized with the Web Audio API directly — no .mp3
 * assets to bundle or fetch, zero added bytes, works completely offline.
 * Defaults to OFF: sound should be an opt-in delight, never a surprise.
 */
export function useSound() {
  const [enabled, setEnabled] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true'
    } catch {
      return false
    }
  })
  const ctxRef = useRef(null)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(enabled))
    } catch {
      /* ignore */
    }
  }, [enabled])

  const getCtx = useCallback(() => {
    if (!ctxRef.current) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) return null
      ctxRef.current = new AudioCtx()
    }
    return ctxRef.current
  }, [])

  const beep = useCallback((freqs, durationMs = 90) => {
    if (!enabled) return
    const ctx = getCtx()
    if (!ctx) return
    freqs.forEach((freq, i) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'sine'
      osc.frequency.value = freq
      gain.gain.value = 0.06
      osc.connect(gain)
      gain.connect(ctx.destination)
      const startAt = ctx.currentTime + i * (durationMs / 1000)
      osc.start(startAt)
      gain.gain.exponentialRampToValueAtTime(0.0001, startAt + durationMs / 1000)
      osc.stop(startAt + durationMs / 1000)
    })
  }, [enabled, getCtx])

  const playSuccess = useCallback(() => beep([523, 659, 784], 110), [beep])
  const playFailure = useCallback(() => beep([330, 261], 140), [beep])
  const playTick = useCallback(() => beep([440], 40), [beep])

  return { enabled, setEnabled, playSuccess, playFailure, playTick }
}
