import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import './styles/index.css'
import App from './App.jsx'
import { queryClient } from './lib/queryClient'

// Remove the instant-paint HTML skeleton (see index.html) now that React
// has real content ready to mount in its place.
const bootSkeleton = document.getElementById('boot-skeleton')
if (bootSkeleton) bootSkeleton.remove()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
