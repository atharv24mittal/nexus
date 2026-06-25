/**
 * Pure CSS animated background: a faint grid (nodding to the
 * oscilloscope/debugger visual identity) plus two slowly-drifting glow
 * blobs. Everything here is a CSS @keyframes transform/opacity animation —
 * zero per-frame JavaScript, so it costs nothing on the main thread and is
 * compositor-accelerated by the browser. Disabled entirely under
 * prefers-reduced-motion (see the media query in index.css, which already
 * zeroes out all animation-duration globally).
 */
export default function AnimatedBackground() {
  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 -z-10 overflow-hidden pointer-events-none"
      style={{ background: 'var(--color-bg)' }}
    >
      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage:
            'linear-gradient(var(--color-border-bright) 1px, transparent 1px), linear-gradient(90deg, var(--color-border-bright) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: 600, height: 600, top: '-15%', left: '-10%',
          background: 'radial-gradient(circle, var(--color-amber-dim) 0%, transparent 70%)',
          opacity: 0.12,
          animation: 'drift-a 22s ease-in-out infinite',
        }}
      />
      <div
        className="absolute rounded-full"
        style={{
          width: 700, height: 700, bottom: '-20%', right: '-15%',
          background: 'radial-gradient(circle, var(--color-dusty-dim) 0%, transparent 70%)',
          opacity: 0.1,
          animation: 'drift-b 26s ease-in-out infinite',
        }}
      />
      <style>{`
        @keyframes drift-a {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(60px, 40px) scale(1.08); }
        }
        @keyframes drift-b {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(-50px, -30px) scale(1.1); }
        }
      `}</style>
    </div>
  )
}
