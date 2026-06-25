const BASE_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/+$/, "");

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function parseValidationDetail(body) {
  if (Array.isArray(body.detail)) {
    // FastAPI/Pydantic validation errors: a list of {loc, msg, type}.
    // Turn that into something a person can actually act on, e.g.
    // "code: Field required" instead of a stringified object.
    return body.detail
      .map((e) => `${(e.loc || []).filter((p) => p !== 'body').join('.')}: ${e.msg}`)
      .join('; ')
  }
  if (typeof body.detail === 'string') return body.detail
  if (body.detail) return JSON.stringify(body.detail)
  return null
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`
    if (res.status === 429) {
      const retryAfter = res.headers.get('Retry-After')
      detail = retryAfter
        ? `Rate limit hit. Try again in ${retryAfter}s.`
        : 'Rate limit hit. Try again shortly.'
    } else {
      try {
        const body = await res.json()
        detail = parseValidationDetail(body) || detail
      } catch {
        /* response wasn't JSON, keep generic message */
      }
    }
    throw new ApiError(detail, res.status)
  }
  return res.json()
}

/**
 * Consumes a Server-Sent Events POST endpoint via fetch's streaming body
 * reader (not the native EventSource API, which can't send a POST body).
 * Calls onEvent(parsedJson) for every "data: ..." line as it arrives —
 * genuinely incremental, not buffered until the response finishes.
 */
async function streamRequest(path, body, onEvent, { signal } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`
    try {
      const responseBody = await res.json()
      detail = parseValidationDetail(responseBody) || detail
    } catch {
      /* ignore */
    }
    throw new ApiError(detail, res.status)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? '' // last piece may be incomplete, keep buffering it

    for (const frame of frames) {
      const line = frame.split('\n').find((l) => l.startsWith('data: '))
      if (!line) continue
      try {
        onEvent(JSON.parse(line.slice('data: '.length)))
      } catch {
        /* malformed frame - skip rather than crash the whole stream */
      }
    }
  }
}

export const api = {
  getProblems: () => request('/problems'),
  getStats: () => request('/stats'),
  solve: (problemId) =>
    request('/solve', { method: 'POST', body: JSON.stringify({ problem_id: problemId }) }),
  solveStream: (problemId, onEvent, opts) =>
    streamRequest('/solve/stream', { problem_id: problemId }, onEvent, opts),
  checkCustomCode: (problemId, code) =>
    request('/check', { method: 'POST', body: JSON.stringify({ problem_id: problemId, code }) }),
  explain: (problemId, code) =>
    request('/explain', { method: 'POST', body: JSON.stringify({ problem_id: problemId, code }) }),
  hint: (problemId, code, errorMessage) =>
    request('/hint', {
      method: 'POST',
      body: JSON.stringify({ problem_id: problemId, code, error_message: errorMessage }),
    }),
  getHistory: (limit = 20) => request(`/history?limit=${limit}`),
  getHistoryStats: () => request('/history/stats'),
  getSharedResult: (resultId) => request(`/result/${resultId}`),
  health: () => request('/health'),
}

export { ApiError, BASE_URL }
