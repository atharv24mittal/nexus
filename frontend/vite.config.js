import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('monaco-editor') || id.includes('@monaco-editor')) return 'monaco'
          if (id.includes('node_modules/react') || id.includes('@tanstack/react-query')) return 'vendor'
          if (id.includes('framer-motion')) return 'motion'
        },
      },
    },
  },
  server: {
    port: 5173,
  },
})
