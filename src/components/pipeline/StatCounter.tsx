'use client';

import { useEffect, useRef, useState } from 'react';

type StatCounterProps = {
  value: number;
  label: string;
  suffix?: string;
  prefix?: string;
  decimals?: number;
  accentColor?: string;
};

export default function StatCounter({
  value,
  label,
  suffix = '',
  prefix = '',
  decimals = 0,
  accentColor = '#38bdf8',
}: StatCounterProps) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const started = useRef(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const duration = 1400;
          const steps = 50;
          const increment = value / steps;
          let current = 0;
          const interval = setInterval(() => {
            current += increment;
            if (current >= value) {
              setDisplay(value);
              clearInterval(interval);
            } else {
              setDisplay(current);
            }
          }, duration / steps);
        }
      },
      { threshold: 0.5 },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [value]);

  const formatted = display.toFixed(decimals);

  return (
    <div ref={ref} className="text-center">
      <p
        className="font-display text-3xl lg:text-4xl font-bold mb-1 tabular-nums"
        style={{ color: accentColor }}
      >
        {prefix}{formatted}{suffix}
      </p>
      <p className="text-xs text-slate-500 font-medium tracking-wide uppercase font-mono-custom">
        {label}
      </p>
    </div>
  );
}
