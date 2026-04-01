'use client';

import { motion } from 'framer-motion';
import { fadeUp, heroStagger } from '@/lib/animations';
import StatCounter from './StatCounter';

const stats = [
  { value: 12, label: 'Stages', suffix: '', accentColor: '#38bdf8' },
  { value: 20000, label: 'Price Records', suffix: '+', accentColor: '#34d399' },
  { value: 48, label: 'Tests', suffix: '', accentColor: '#818cf8' },
  { value: 1755, label: 'Docs Lines', suffix: '', accentColor: '#fbbf24' },
];

const pipeline = ['Yahoo Finance', 'Ingestor', 'PostgreSQL', 'Lakehouse', 'DuckDB', 'FastAPI', 'Portfolio'];

export default function PipelineHero() {
  return (
    <section className="relative min-h-[70vh] flex items-center overflow-hidden">
      {/* Background glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-radial from-cyan-400/8 via-indigo-400/4 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[500px] h-[300px] bg-gradient-radial from-green-400/6 to-transparent rounded-full blur-3xl" />
      </div>

      {/* Grid overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage: `linear-gradient(rgba(56,189,248,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.8) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8 pt-32 pb-16 w-full">
        <motion.div
          variants={heroStagger}
          initial="hidden"
          animate="visible"
          className="flex flex-col items-center text-center"
        >
          <motion.p variants={fadeUp} className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-4">
            End-to-End Data Engineering Portfolio
          </motion.p>

          <motion.h1 variants={fadeUp} className="font-display text-5xl sm:text-6xl lg:text-7xl font-black leading-none mb-6">
            <span className="block text-slate-100">Oil Price</span>
            <span className="block text-gradient-cyan-indigo">Pipeline</span>
          </motion.h1>

          <motion.p variants={fadeUp} className="text-base lg:text-lg text-slate-400 leading-relaxed max-w-2xl mb-10 font-light">
            12 sequential stages from raw market data to interactive portfolio. PostgreSQL data warehouse,
            DuckDB/Parquet medallion lakehouse, FastAPI dual-backend, Docker, Kubernetes, CI/CD, and Prometheus monitoring.
          </motion.p>

          {/* Pipeline flow */}
          <motion.div variants={fadeUp} className="flex flex-wrap items-center justify-center gap-0 mb-14 overflow-x-auto">
            {pipeline.map((step, i) => (
              <div key={step} className="flex items-center">
                <span className="px-3 py-1.5 rounded-lg text-xs font-mono-custom font-semibold bg-white/5 border border-white/8 text-slate-300 whitespace-nowrap">
                  {step}
                </span>
                {i < pipeline.length - 1 && (
                  <svg className="w-5 h-4 text-slate-600 mx-1 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </div>
            ))}
          </motion.div>

          {/* Stats */}
          <motion.div variants={fadeUp} className="grid grid-cols-2 sm:grid-cols-4 gap-8 lg:gap-16">
            {stats.map((s) => (
              <StatCounter key={s.label} {...s} />
            ))}
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
