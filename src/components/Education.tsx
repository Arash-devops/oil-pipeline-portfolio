'use client';

import { motion } from 'framer-motion';
import { fadeUp, staggerContainer, viewportOptions } from '@/lib/animations';
import { degrees } from '@/data/education';

export default function Education() {
  return (
    <section id="education" className="relative py-24 lg:py-32">
      <div className="section-divider absolute top-0 inset-x-0" />

      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-16"
        >
          <p className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-3">
            03 / Education
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Academic Journey
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Three postgraduate degrees across three countries, each adding a distinct
            technical dimension.
          </p>
        </motion.div>

        {/* Timeline */}
        <div className="relative max-w-3xl mx-auto">
          {/* Connecting line */}
          <div className="absolute left-6 md:left-1/2 top-0 bottom-0 w-px -translate-x-1/2">
            <div className="h-full w-full bg-gradient-to-b from-cyan-400/40 via-indigo-400/40 to-rose-400/40" />
          </div>

          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={viewportOptions}
            className="space-y-12"
          >
            {degrees.map((degree, index) => (
              <motion.div
                key={degree.id}
                variants={fadeUp}
                className={`relative flex gap-8 md:gap-0 ${
                  index % 2 === 0 ? 'md:flex-row' : 'md:flex-row-reverse'
                }`}
              >
                {/* Content card */}
                <div
                  className={`flex-1 ${
                    index % 2 === 0
                      ? 'md:pr-12 md:text-right'
                      : 'md:pl-12 md:text-left'
                  } pl-12 md:pl-0`}
                >
                  <motion.div
                    whileHover={{ y: -4, transition: { duration: 0.2 } }}
                    className="p-6 rounded-2xl bg-[#111827] border border-white/5 hover:border-white/10 transition-all duration-300 group"
                    style={{
                      boxShadow: `0 0 30px ${degree.dotColor}10`,
                    }}
                  >
                    {/* Status badge */}
                    <div className={`flex items-center gap-2 mb-3 ${index % 2 === 0 ? 'md:justify-end' : ''}`}>
                      {degree.status === 'current' ? (
                        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-400/10 border border-green-400/20 text-xs text-green-400 font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                          Currently Studying
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-slate-400 font-medium">
                          Completed
                        </span>
                      )}
                    </div>

                    {/* Degree */}
                    <p className="font-mono-custom text-xs tracking-widest uppercase mb-1" style={{ color: degree.dotColor }}>
                      {degree.degree} · {degree.period}
                    </p>
                    <h3 className="font-display text-xl font-bold text-slate-100 mb-1">
                      {degree.field}
                    </h3>
                    <p className="text-sm font-medium text-slate-300 mb-0.5">
                      {degree.institution}
                    </p>
                    <p className="text-xs text-slate-500 mb-3">📍 {degree.location}</p>

                    {degree.score && (
                      <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-xl mb-4 ${
                        degree.id === 'data-science'
                          ? 'bg-indigo-400/10 border border-indigo-400/20'
                          : 'bg-white/5 border border-white/10'
                      }`}>
                        <span className="text-xs font-semibold" style={{ color: degree.dotColor }}>
                          🏆 {degree.score}
                        </span>
                      </div>
                    )}

                    <p className="text-sm text-slate-400 leading-relaxed">
                      {degree.description}
                    </p>

                    {/* Tags */}
                    <div className={`flex flex-wrap gap-1.5 mt-4 ${index % 2 === 0 ? 'md:justify-end' : ''}`}>
                      {degree.tags.map((tag) => (
                        <span
                          key={tag}
                          className="px-2 py-0.5 text-xs font-mono-custom rounded-full border"
                          style={{
                            color: `${degree.dotColor}aa`,
                            borderColor: `${degree.dotColor}25`,
                            backgroundColor: `${degree.dotColor}08`,
                          }}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </motion.div>
                </div>

                {/* Center dot */}
                <div className="absolute left-6 md:left-1/2 top-8 -translate-x-1/2 z-10">
                  <div
                    className="w-4 h-4 rounded-full border-2 border-[#0a0e17]"
                    style={{ backgroundColor: degree.dotColor, boxShadow: `0 0 12px ${degree.dotColor}80` }}
                  />
                </div>

                {/* Empty side for alignment */}
                <div className="hidden md:block flex-1" />
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
