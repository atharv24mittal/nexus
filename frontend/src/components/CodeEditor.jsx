import { Suspense, lazy } from 'react'

const Editor = lazy(() => import('@monaco-editor/react'))

function EditorSkeleton() {
  return (
    <div className="h-full w-full p-4 space-y-2.5">
      {[100, 85, 92, 70, 60, 88, 45].map((w, i) => (
        <div
          key={i}
          className="h-3.5 rounded shimmer-bg"
          style={{ width: `${w}%`, animationDelay: `${i * 80}ms` }}
        />
      ))}
    </div>
  )
}

export default function CodeEditor({ value, onChange, readOnly = false }) {
  return (
    <Suspense fallback={<EditorSkeleton />}>
      <Editor
        height="100%"
        defaultLanguage="python"
        theme="vs-dark"
        value={value}
        onChange={onChange}
        options={{
          readOnly,
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 13,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          padding: { top: 14, bottom: 14 },
          renderLineHighlight: readOnly ? 'none' : 'line',
          cursorBlinking: 'smooth',
          smoothScrolling: true,
        }}
      />
    </Suspense>
  )
}
