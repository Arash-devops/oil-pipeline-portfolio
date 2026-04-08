'use client';

import { motion } from 'framer-motion';
import { fadeUp, slideInLeft, slideInRight, staggerContainer, viewportOptions } from '@/lib/animations';

const highlights = [
  {
    icon: '🎓',
    title: 'Triple Master\'s',
    description: 'MSc Cyber Security, MSc Data Science (Distinction), MSc Computer Hardware Engineering — a rare multidisciplinary breadth.',
    color: 'from-cyan-500/10 to-cyan-500/5',
    border: 'border-cyan-500/20',
    iconBg: 'bg-cyan-500/10',
  },
  {
    icon: '🌍',
    title: 'International',
    description: 'Studied and worked across Iran, the United Kingdom, and Germany — bringing global perspective to every project.',
    color: 'from-indigo-500/10 to-indigo-500/5',
    border: 'border-indigo-500/20',
    iconBg: 'bg-indigo-500/10',
  },
  {
    icon: '⚡',
    title: 'Full-Stack Mindset',
    description: 'From bare-metal hardware to cloud infrastructure to pixel-perfect UIs — comfortable navigating the entire stack.',
    color: 'from-green-500/10 to-green-500/5',
    border: 'border-green-500/20',
    iconBg: 'bg-green-500/10',
  },
  {
    icon: '🔒',
    title: 'Security-First',
    description: 'A current MSc in Cyber Security ensures security is baked in at the architecture level — not bolted on at the end.',
    color: 'from-amber-500/10 to-amber-500/5',
    border: 'border-amber-500/20',
    iconBg: 'bg-amber-500/10',
  },
];

export default function About() {
  return (
    <section id="about" className="relative py-24 lg:py-32">
      {/* Divider */}
      <div className="section-divider absolute top-0 inset-x-0" />

      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-16"
        >
          <p className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-3">
            01 / About
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100">
            Who I Am
          </h2>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-start">
          {/* Left: Bio */}
          <motion.div
            variants={slideInLeft}
            initial="hidden"
            whileInView="visible"
            viewport={viewportOptions}
            className="space-y-5"
          >
            <p className="text-slate-300 text-lg leading-relaxed">
              I&apos;m <span className="text-slate-100 font-semibold">Arash Razban</span>, a data
              engineering and backend development enthusiast based in{' '}
              <span className="text-cyan-400 font-medium">Berlin, Germany</span>. I hold an{' '}
              <span className="text-indigo-400 font-medium">MSc in Data Science</span> from Ulster
              University (<span className="text-slate-200 font-medium">Distinction</span>), an{' '}
              <span className="text-amber-400 font-medium">MSc in Computer Hardware Engineering</span>,
              and I&apos;m currently studying{' '}
              <span className="text-rose-400 font-medium">Cyber Security</span>.
            </p>

            <p className="text-slate-400 leading-relaxed">
              I love building things end-to-end — from designing database schemas and data pipelines
              to containerising services and setting up CI/CD. My portfolio project (a 12-stage{' '}
              <span className="text-slate-200">Oil Price Data Pipeline</span>) is how I teach myself
              by doing: PostgreSQL, DuckDB, FastAPI, Docker, Kubernetes, Prometheus, and more.
            </p>

            <p className="text-slate-400 leading-relaxed">
              I&apos;m actively looking for{' '}
              <span className="text-slate-200">internships, working student positions, or junior roles</span>{' '}
              in data engineering, backend development, or DevOps. I&apos;m eager to learn from
              experienced teams, contribute meaningfully, and keep growing as an engineer.
            </p>

            {/* Location / availability badge */}
            <div className="flex flex-wrap gap-3 pt-2">
              <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-slate-300">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                Open to opportunities
              </span>
              <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-slate-300">
                📍 Berlin, Germany
              </span>
              <span className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-slate-300">
                🌐 Remote / On-site
              </span>
            </div>
          </motion.div>

          {/* Right: 2×2 highlight cards */}
          <motion.div
            variants={slideInRight}
            initial="hidden"
            whileInView="visible"
            viewport={viewportOptions}
          >
            <motion.div
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={viewportOptions}
              className="grid grid-cols-2 gap-4"
            >
              {highlights.map((item) => (
                <motion.div
                  key={item.title}
                  variants={fadeUp}
                  whileHover={{ y: -4, transition: { duration: 0.2 } }}
                  className={`p-5 rounded-2xl bg-gradient-to-br ${item.color} border ${item.border} group cursor-default`}
                >
                  <div className={`w-10 h-10 rounded-xl ${item.iconBg} flex items-center justify-center text-xl mb-4`}>
                    {item.icon}
                  </div>
                  <h3 className="font-display text-base font-semibold text-slate-100 mb-2">
                    {item.title}
                  </h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    {item.description}
                  </p>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
