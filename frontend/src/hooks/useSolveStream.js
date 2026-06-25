import { useState, useCallback, useRef } from 'react'
import { api, ApiError } from '../api/client'

const REDUCED_MOTION = typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function initialState() {
  return {
    isStreaming: false,
    phase: 'idle', // idle | generating | executing | verifying | retrieving | done
    attemptNumber: 0,
    attempts: [],       // completed attempt records, in order
    currentCode: '',
    currentTrace: [],
    currentStdout: '',
    currentVerification: null,
    currentComplexity: null,
    finalResult: null,  // set once the stream finishes
    error: null,
  }
}

/**
 * Drives the live solve view directly from the server's real-time event
 * stream (see backend POST /solve/stream). Every field this hook exposes
 * reflects something that has ALREADY happened on the server at the moment
 * it's set — there is no client-side pacing or replay involved.
 */
export function useSolveStream() {
  const [state, setState] = useState(initialState)
  const abortRef = useRef(null)
  const sessionIdRef = useRef(0)
  const [sessionId, setSessionId] = useState(0)

  const start = useCallback((problemId) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    sessionIdRef.current += 1
    setSessionId(sessionIdRef.current)

    setState({ ...initialState(), isStreaming: true, phase: 'generating' })

    api.solveStream(problemId, (event) => {
      setState((prev) => {
        switch (event.event) {
          case 'attempt_start':
            return { ...prev, attemptNumber: event.attempt_number, phase: 'generating' }
          case 'generating':
            return { ...prev, phase: 'generating' }
          case 'code_generated':
            return { ...prev, currentCode: event.code, phase: 'executing' }
          case 'executing':
            return { ...prev, phase: 'executing' }
          case 'execution_complete':
            return { ...prev, currentTrace: event.trace, currentStdout: event.stdout, phase: 'verifying' }
          case 'verifying':
            return { ...prev, phase: 'verifying' }
          case 'complexity_check':
            return { ...prev, currentComplexity: event.complexity_check }
          case 'verification_result':
            return {
              ...prev,
              phase: 'verifying',
              currentVerification: {
                passed: event.passed,
                message: event.message,
                method: event.method,
                violated_constraint: event.violated_constraint,
                counterexample: event.counterexample,
              },
            }
          case 'attempt_complete':
            return {
              ...prev,
              attempts: [...prev.attempts, event.attempt],
              phase: event.passed ? 'verifying' : 'retrieving',
            }
          case 'retrieving_fixes':
            return { ...prev, phase: 'retrieving' }
          case 'final_result':
            return {
              ...prev,
              isStreaming: false,
              phase: 'done',
              finalResult: event,
              currentCode: event.final_code ?? prev.currentCode,
            }
          case 'stream_error':
            return { ...prev, isStreaming: false, phase: 'done', error: event.message }
          default:
            return prev
        }
      })
    }, { signal: controller.signal }).catch((err) => {
      if (err.name === 'AbortError') return
      const message = err instanceof ApiError ? err.message : 'Connection to NEXUS lost mid-stream.'
      setState((prev) => ({ ...prev, isStreaming: false, phase: 'done', error: message }))
    })
  }, [])

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setState(initialState())
  }, [])

  return { ...state, sessionId, start, reset, reducedMotion: REDUCED_MOTION }
}
