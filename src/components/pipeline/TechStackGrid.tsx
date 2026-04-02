'use client';

import { motion } from 'framer-motion';
import { fadeUp, viewportOptions } from '@/lib/animations';

type Tech = {
  name: string;
  role: string;
  category: string;
  color: string;
};

const techs: Tech[] = [
  { name: 'PostgreSQL', role: 'Data warehouse — Star Schema, stored procedures', category: 'Data', color: '#38bdf8' },
  { name: 'DuckDB', role: 'In-process analytics over Parquet (Gold layer)', category: 'Data', color: '#38bdf8' },
  { name: 'Apache Parquet', role: 'Columnar storage format for lakehouse layers', category: 'Data', color: '#38bdf8' },
  { name: 'PyArrow', role: 'Schema-typed Parquet write with Hive partitioning', category: 'Data', color: '#38bdf8' },
  { name: 'yfinance', role: 'Yahoo Finance OHLCV data source', category: 'Data', color: '#38bdf8' },
  { name: 'FastAPI', role: 'Async REST API with dual PostgreSQL + DuckDB backends', category: 'API', color: '#818cf8' },
  { name: 'Pydantic v2', role: 'Request validation, settings management', category: 'API', color: '#818cf8' },
  { name: 'psycopg v3', role: 'Async PostgreSQL adapter with connection pooling', category: 'API', color: '#818cf8' },
  { name: 'structlog', role: 'Structured JSON logging', category: 'API', color: '#818cf8' },
  { name: 'Docker', role: 'Multi-service containerization with named volumes', category: 'Infra', color: '#34d399' },
  { name: 'Kubernetes', role: '29 manifests: Deployments, Jobs, PVCs, HPA', category: 'Infra', color: '#34d399' },
  { name: 'Helm', role: 'Templated chart with environment-specific values', category: 'Infra', color: '#34d399' },
  { name: 'Prometheus', role: '5 metrics scraped from MetricsMiddleware', category: 'Infra', color: '#34d399' },
  { name: 'Grafana', role: 'Auto-provisioned 10-panel API dashboard', category: 'Infra', color: '#34d399' },
  { name: 'GitHub Actions', role: '6-job CI/CD: lint → test → build → deploy', category: 'Infra', color: '#34d399' },
  { name: 'ruff', role: 'Python linter + formatter (rules E/W/F/I/UP/B/SIM)', category: 'Infra', color: '#34d399' },
  { name: 'Next.js 14', role: 'Static portfolio with App Router', category: 'Frontend', color: '#fbbf24' },
  { name: 'Recharts', role: 'Interactive data visualisation charts', category: 'Frontend', color: '#fbbf24' },
  { name: 'Framer Motion', role: 'Scroll-triggered animations and transitions', category: 'Frontend', color: '#fbbf24' },
  { name: 'Mermaid', role: '6 architecture diagrams exported to PNG', category: 'Frontend', color: '#fbbf24' },
];

const categoryOrder = ['Data', 'API', 'Infra', 'Frontend'];

export default function TechStackGrid() {
  const grouped = categoryOrder.map((cat) => ({
    cat,
    items: techs.filter((t) => t.category === cat),
  }));

  return (
    <section className="relative py-24 lg:py-32 bg-[#0d1117]">
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
            Technologies
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Full Stack
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            {techs.length} technologies across data engineering, API, infrastructure, and frontend.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-8">
          {grouped.map(({ cat, items }) => (
            <motion.div
              key={cat}
              variants={fadeUp}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.1 }}
            >
              <p
                className="text-xs font-mono-custom font-semibold uppercase tracking-[0.2em] mb-4"
                style={{ color: items[0]?.color }}
              >
                {cat}
              </p>
              <div className="flex flex-col gap-2">
                {items.map((tech) => (
                  <div
                    key={tech.name}
                    className="flex items-start gap-3 p-3 rounded-xl border border-white/5 bg-[#111827] hover:border-white/10 transition-colors duration-200"
                  >
                    <span
                      className="flex-shrink-0 w-1.5 h-1.5 rounded-full mt-1.5"
                      style={{ backgroundColor: tech.color }}
                    />
                    <div className="min-w-0">
                      <span className="text-sm font-mono-custom font-semibold text-slate-200">
                        {tech.name}
                      </span>
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{tech.role}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mt-16"
        >
          <a
            href="https://github.com/Arash-devops/oil-pipeline-portfolio"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 text-sm font-medium text-slate-300 border border-white/10 rounded-xl hover:bg-white/5 hover:border-white/20 transition-all duration-200"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            View source on GitHub
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </a>
        </motion.div>
      </div>
    </section>
  );
}
