import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { queryKeys } from '../lib/queryClient'

export function useProblems() {
  return useQuery({
    queryKey: queryKeys.problems,
    queryFn: api.getProblems,
    staleTime: Infinity, // the problem bank is fixed for the lifetime of a deployment
  })
}

export function useStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: api.getStats,
    staleTime: 60 * 1000,
  })
}

export function useSolve() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (problemId) => api.solve(problemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.stats })
      queryClient.invalidateQueries({ queryKey: queryKeys.history })
      queryClient.invalidateQueries({ queryKey: queryKeys.historyStats })
    },
  })
}

export function useCheckCode() {
  return useMutation({
    mutationFn: ({ problemId, code }) => api.checkCustomCode(problemId, code),
  })
}

export function useExplain() {
  return useMutation({
    mutationFn: ({ problemId, code }) => api.explain(problemId, code),
  })
}

export function useHint() {
  return useMutation({
    mutationFn: ({ problemId, code, errorMessage }) => api.hint(problemId, code, errorMessage),
  })
}

export function useHistory(limit = 20) {
  return useQuery({
    queryKey: [...queryKeys.history, limit],
    queryFn: () => api.getHistory(limit),
    staleTime: 15 * 1000,
  })
}

export function useHistoryStats() {
  return useQuery({
    queryKey: queryKeys.historyStats,
    queryFn: api.getHistoryStats,
    staleTime: 15 * 1000,
  })
}

export function useSharedResult(resultId) {
  return useQuery({
    queryKey: [...queryKeys.sharedResult, resultId],
    queryFn: () => api.getSharedResult(resultId),
    enabled: Boolean(resultId),
    staleTime: Infinity, // a past result never changes
    retry: false,
  })
}
