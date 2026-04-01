'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeUp, viewportOptions } from '@/lib/animations';
import { pipelineStages, categoryColors, categoryLabels, type PipelineStage } from '@/data/pipeline-stages';

const categories = ['all', 'data', 'infrastructure', 'api', 'frontend'] as const;
type CategoryFilter = typeof categories[number];

export default function StageExplorer() {
  const [activeCategory, setActiveCategory] = useState<CategoryFilter>('all');
  const [openStage, setOpenStage] = useState<string | null>('schema-design');

  const filtered = activeCategory === 'all'
    ? pipelineStages
    : pipelineStages.filter((s) => s.category === activeCategory);

  return (
    <section className="relative py-24 lg:py-32 bg-[#0a0e17]">
      <div className="section-divider absolute top-0 inset-x-0" />

      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-16"
        >
          <p className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-3">
            Stage Explorer
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            12 Stages
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Click any stage to expand the implementation details, tech stack, and key decisions.
          </p>
        </motion.div>

        {/* Category filters */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="flex flex-wrap justify-center gap-2 mb-10"
        >
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => {
                setActiveCategory(cat);
                setOpenStage(null);
              }}
              className="px-4 py-1.5 rounded-full text-xs font-mono-custom font-semibold border transition-all duration-200"
              style={
                activeCategory === cat
                  ? {
                      color: cat === 'all' ? '#38bdf8' : categoryColors[cat as PipelineStage['category']],
                      borderColor: cat === 'all' ? '#38bdf840' : `${categoryColors[cat as PipelineStage['category']]}40`,
                      backgroundColor: cat === 'all' ? '#38bdf812' : `${categoryColors[cat as PipelineStage['category']]}12`,
                    }
                  : { color: '#64748b', borderColor: '#1e293b', backgroundColor: 'transparent' }
              }
            >
              {cat === 'all' ? 'All Stages' : categoryLabels[cat as PipelineStage['category']]}
            </button>
          ))}
        </motion.div>

        {/* Stage accordion */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="flex flex-col gap-3"
        >
          <AnimatePresence mode="popLayout">
            {filtered.map((stage) => {
              const isOpen = openStage === stage.id;
              return (
                <motion.div
                  key={stage.id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="rounded-2xl border overflow-hidden"
                  style={{
                    borderColor: isOpen ? `${stage.accentColor}30` : 'rgba(255,255,255,0.05)',
                    backgroundColor: isOpen ? `${stage.accentColor}06` : '#111827',
                  }}
                >
                  {/* Header */}
                  <button
                    className="w-full flex items-center gap-4 px-6 py-4 text-left group"
                    onClick={() => setOpenStage(isOpen ? null : stage.id)}
                  >
                    {/* Stage number */}
                    <span
                      className="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono-custom font-bold border"
                      style={{
                        color: stage.accentColor,
                        borderColor: `${stage.accentColor}40`,
                        backgroundColor: `${stage.accentColor}12`,
                      }}
                    >
                      {String(stage.number).padStart(2, '0')}
                    </span>

                    {/* Title */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 flex-wrap">
                        <span className="font-display font-bold text-slate-100 group-hover:text-white transition-colors">
                          {stage.title}
                        </span>
                        <span className="text-xs text-slate-500 font-mono-custom">{stage.subtitle}</span>
                      </div>
                    </div>

                    {/* Category badge */}
                    <span
                      className="hidden sm:inline-flex px-2 py-0.5 rounded-full text-xs font-mono-custom border flex-shrink-0"
                      style={{
                        color: categoryColors[stage.category],
                        borderColor: `${categoryColors[stage.category]}30`,
                        backgroundColor: `${categoryColors[stage.category]}10`,
                      }}
                    >
                      {categoryLabels[stage.category]}
                    </span>

                    {/* Chevron */}
                    <motion.svg
                      animate={{ rotate: isOpen ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                      className="w-4 h-4 flex-shrink-0 text-slate-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </motion.svg>
                  </button>

                  {/* Expanded content */}
                  <AnimatePresence>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-6 pt-2 border-t border-white/5">
                          <div className="grid md:grid-cols-2 gap-6">
                            {/* Description */}
                            <div>
                              <p className="text-sm text-slate-400 leading-relaxed mb-4">
                                {stage.description}
                              </p>
                              {/* Tech stack */}
                              <div className="flex flex-wrap gap-1.5">
                                {stage.techStack.map((tech) => (
                                  <span
                                    key={tech}
                                    className="px-2 py-0.5 text-xs font-mono-custom rounded-full bg-white/5 border border-white/8 text-slate-400"
                                  >
                                    {tech}
                                  </span>
                                ))}
                              </div>
                            </div>

                            {/* Highlights */}
                            <div>
                              <p className="text-xs font-mono-custom text-slate-500 uppercase tracking-wider mb-3">
                                Key Highlights
                              </p>
                              <ul className="flex flex-col gap-2">
                                {stage.highlights.map((h) => (
                                  <li key={h} className="flex items-start gap-2 text-sm text-slate-300">
                                    <span className="flex-shrink-0 w-1 h-1 rounded-full mt-2" style={{ backgroundColor: stage.accentColor }} />
                                    {h}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </AnimatePresence>
        </motion.div>
      </div>
    </section>
  );
}
