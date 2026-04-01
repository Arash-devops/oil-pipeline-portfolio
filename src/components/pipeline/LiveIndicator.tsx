'use client';

type LiveIndicatorProps = {
  isLive: boolean;
  loading?: boolean;
};

export default function LiveIndicator({ isLive, loading = false }: LiveIndicatorProps) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono-custom border border-white/10 text-slate-500">
        <span className="w-1.5 h-1.5 rounded-full bg-slate-600 animate-pulse" />
        Connecting…
      </span>
    );
  }

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono-custom border"
      style={
        isLive
          ? { color: '#34d399', borderColor: '#34d39940', backgroundColor: '#34d39912' }
          : { color: '#94a3b8', borderColor: '#94a3b820', backgroundColor: '#94a3b808' }
      }
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{
          backgroundColor: isLive ? '#34d399' : '#64748b',
          boxShadow: isLive ? '0 0 6px #34d399' : 'none',
          animation: isLive ? 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite' : 'none',
        }}
      />
      {isLive ? 'Live API' : 'Sample Data'}
    </span>
  );
}
