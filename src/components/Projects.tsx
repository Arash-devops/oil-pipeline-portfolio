'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { fadeUp, staggerContainerFast, viewportOptions } from '@/lib/animations';
import { projects } from '@/data/projects';

export default function Projects() {
  return (
    <section id="projects" className="relative py-24 lg:py-32 bg-[#0d1117]">
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
            04 / Projects
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Selected Work
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            A curated set of projects spanning data pipelines, cloud infrastructure, and APIs.
            Links will be updated as repositories are published.
          </p>
        </motion.div>

        {/* Grid */}
        <motion.div
          variants={staggerContainerFast}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {projects.map((project) => (
            <motion.article
              key={project.id}
              variants={fadeUp}
              whileHover={{ y: -6, transition: { duration: 0.2 } }}
              className="group flex flex-col rounded-2xl overflow-hidden border border-white/5 bg-[#111827] hover:border-white/10 transition-all duration-300"
              style={{
                boxShadow: project.featured
                  ? `0 0 40px ${project.accentColor}10`
                  : 'none',
              }}
            >
              {/* Gradient preview */}
              <div className={`relative h-36 bg-gradient-to-br ${project.gradient} overflow-hidden`}>
                {/* Pattern overlay */}
                <div
                  className="absolute inset-0 opacity-10"
                  style={{
                    backgroundImage: `repeating-linear-gradient(45deg, ${project.accentColor} 0, ${project.accentColor} 1px, transparent 0, transparent 50%)`,
                    backgroundSize: '12px 12px',
                  }}
                />
                {/* Featured badge */}
                {project.featured && (
                  <div
                    className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-xs font-mono-custom font-semibold"
                    style={{
                      color: project.accentColor,
                      backgroundColor: `${project.accentColor}20`,
                      border: `1px solid ${project.accentColor}40`,
                    }}
                  >
                    Featured
                  </div>
                )}
                {/* Corner glow */}
                <div
                  className="absolute bottom-0 left-0 w-40 h-40 rounded-full blur-2xl opacity-30"
                  style={{ backgroundColor: project.accentColor }}
                />
              </div>

              {/* Content */}
              <div className="flex flex-col flex-1 p-6">
                <h3 className="font-display text-lg font-bold text-slate-100 mb-2 group-hover:text-white transition-colors">
                  {project.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed flex-1 mb-4">
                  {project.description}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1.5 mb-5">
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 text-xs font-mono-custom rounded-full bg-white/5 border border-white/8 text-slate-400"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Links */}
                <div className="flex items-center gap-3 pt-4 border-t border-white/5">
                  <a
                    href={project.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-xs font-medium text-slate-400 hover:text-slate-100 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                      <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                    </svg>
                    Source
                  </a>
                  {project.liveUrl && (
                    <Link
                      href={project.liveUrl}
                      className="flex items-center gap-1.5 text-xs font-medium transition-colors"
                      style={{ color: project.accentColor }}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      Live Demo
                    </Link>
                  )}
                </div>
              </div>
            </motion.article>
          ))}
        </motion.div>

        {/* CTA */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mt-12"
        >
          <a
            href="https://github.com/Arash-devops"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-slate-300 border border-white/10 rounded-xl hover:bg-white/5 hover:border-white/20 transition-all duration-200"
          >
            View all repositories on GitHub
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </motion.div>
      </div>
    </section>
  );
}
