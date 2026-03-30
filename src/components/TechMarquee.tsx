'use client';

import { marqueeItems } from '@/data/skills';

const doubled = [...marqueeItems, ...marqueeItems];

export default function TechMarquee() {
  return (
    <section className="relative py-12 overflow-hidden bg-[#0a0e17] border-y border-white/5">
      {/* Edge fades */}
      <div className="absolute left-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-r from-[#0a0e17] to-transparent pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-24 z-10 bg-gradient-to-l from-[#0a0e17] to-transparent pointer-events-none" />

      <div className="marquee-track overflow-hidden">
        <div
          className="marquee-inner flex items-center gap-6 whitespace-nowrap animate-marquee"
          style={{ width: 'max-content' }}
        >
          {doubled.map((item, i) => (
            <span
              key={`${item}-${i}`}
              className="flex items-center gap-2 px-5 py-2.5 rounded-full border border-white/[0.08] bg-white/[0.03] font-mono-custom text-sm text-slate-400 hover:text-slate-200 hover:border-white/20 hover:bg-white/[0.06] transition-all duration-200 cursor-default select-none"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/50 flex-shrink-0" />
              {item}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
