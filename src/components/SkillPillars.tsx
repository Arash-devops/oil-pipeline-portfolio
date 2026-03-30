'use client';

import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { fadeUp, staggerContainer, viewportOptions } from '@/lib/animations';
import { pillars } from '@/data/skills';

type ProficiencyBarProps = {
  label: string;
  value: number;
  color: string;
};

function ProficiencyBar({ label, value, color }: ProficiencyBarProps) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: '-60px' });

  return (
    <div ref={ref} className="space-y-1">
      <div className="flex justify-between items-center">
        <span className="text-xs text-slate-400 font-medium">{label}</span>
        <span className="text-xs font-mono-custom" style={{ color }}>{value}%</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: inView ? `${value}%` : 0 }}
          transition={{ duration: 1.2, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.2 }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function SkillPillars() {
  return (
    <section id="skills" className="relative py-24 lg:py-32 bg-[#0d1117]">
      <div className="section-divider absolute top-0 inset-x-0" />

      {/* Background accent */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-radial from-indigo-400/4 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-16"
        >
          <p className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-3">
            02 / Skills
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Four Core Pillars
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto leading-relaxed">
            A deliberate skill stack built across infrastructure, data, backend, and frontend —
            enabling end-to-end ownership of complex technical systems.
          </p>
        </motion.div>

        {/* 2×2 Grid */}
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="grid md:grid-cols-2 gap-6"
        >
          {pillars.map((pillar) => (
            <motion.div
              key={pillar.id}
              variants={fadeUp}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="group relative rounded-2xl overflow-hidden border border-white/5 bg-[#111827]/80 backdrop-blur-sm transition-all duration-300 hover:border-white/10"
              style={{ boxShadow: `0 0 40px ${pillar.bgGlow}` }}
            >
              {/* Colored top border */}
              <div
                className="absolute top-0 inset-x-0 h-[3px]"
                style={{ background: `linear-gradient(90deg, ${pillar.borderColor}, ${pillar.borderColor}60)` }}
              />

              {/* Glow overlay */}
              <div
                className="absolute top-0 inset-x-0 h-32 pointer-events-none"
                style={{
                  background: `linear-gradient(180deg, ${pillar.bgGlow} 0%, transparent 100%)`,
                }}
              />

              <div className="relative p-7">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{pillar.icon}</span>
                      <h3 className={`font-display text-xl font-bold ${pillar.textColor}`}>
                        {pillar.title}
                      </h3>
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed max-w-sm">
                      {pillar.description}
                    </p>
                  </div>
                </div>

                {/* Proficiency bars */}
                <div className="space-y-2.5 mb-6">
                  {pillar.proficiencies.map((p) => (
                    <ProficiencyBar
                      key={p.label}
                      label={p.label}
                      value={p.value}
                      color={pillar.borderColor}
                    />
                  ))}
                </div>

                {/* Tech tags */}
                <div className="flex flex-wrap gap-2">
                  {pillar.technologies.map((tech) => (
                    <span
                      key={tech.name}
                      className="px-2.5 py-1 text-xs font-mono-custom rounded-full border transition-all duration-200 cursor-default"
                      style={{
                        color: `${pillar.borderColor}cc`,
                        borderColor: `${pillar.borderColor}25`,
                        backgroundColor: `${pillar.borderColor}0a`,
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = `${pillar.borderColor}20`;
                        e.currentTarget.style.borderColor = `${pillar.borderColor}50`;
                        e.currentTarget.style.color = pillar.borderColor;
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = `${pillar.borderColor}0a`;
                        e.currentTarget.style.borderColor = `${pillar.borderColor}25`;
                        e.currentTarget.style.color = `${pillar.borderColor}cc`;
                      }}
                    >
                      {tech.name}
                    </span>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
