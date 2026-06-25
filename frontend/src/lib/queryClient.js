import { QueryClient } from '@tanstack/react-query'

/*
  Caching strategy, deliberately tuned for this app's data shapes:

  - /problems barely ever changes (it's a fixed curated bank) -> long
    staleTime, so navigating around the app never re-fetches it.
  - /stats (skill library size, LLM provider) changes slowly but the user
    cares about freshness right after a solve -> short staleTime, and we
    explicitly invalidate it after every successful /solve mutation.
  - /solve and /check are mutations, not cached reads, by nature — every
    click is a genuinely new run. There's nothing to cache there; the
    "speed" lever for those is the backend's own response time, not caching.
*/
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 30 * 60 * 1000,   // keep cached data around for 30 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export const queryKeys = {
  problems: ['problems'],
  stats: ['stats'],
  history: ['history'],
  historyStats: ['historyStats'],
  sharedResult: ['sharedResult'],
}
