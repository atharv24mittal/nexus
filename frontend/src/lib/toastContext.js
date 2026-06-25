import { createContext } from 'react'

// Plain context object, no component/hook here — keeping this file
// component-free is what lets ToastProvider.jsx and useToast.js both
// qualify for Vite's Fast Refresh.
export const ToastContext = createContext(null)
