'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import Image from 'next/image';
import { fadeUp, staggerContainerFast, viewportOptions } from '@/lib/animations';
import DiagramModal from './DiagramModal';

type Diagram = {
  key: string;
  title: string;
  description: string;
  accentColor: string;
};

const diagrams: Diagram[] = [
  {
    key: 'pipeline-overview',
    title: 'Pipeline Overview',
    description: 'End-to-end data flow from Yahoo Finance to portfolio',
    accentColor: '#38bdf8',
  },
  {
    key: 'docker-topology',
    title: 'Docker Topology',
    description: 'Service dependencies, volumes, and port mappings',
    accentColor: '#818cf8',
  },
  {
    key: 'data-warehouse-schema',
    title: 'Data Warehouse Schema',
    description: 'Star schema ER diagram with staging table',
    accentColor: '#34d399',
  },
  {
    key: 'medallion-architecture',
    title: 'Medallion Architecture',
    description: 'Bronze → Silver → Gold transformation flow',
    accentColor: '#fbbf24',
  },
  {
    key: 'cicd-pipeline',
    title: 'CI/CD Pipeline',
    description: 'GitHub Actions jobs, dependencies, and triggers',
    accentColor: '#fb7185',
  },
  {
    key: 'monitoring-stack',
    title: 'Monitoring Stack',
    description: 'Prometheus scrape → Grafana dashboard flow',
    accentColor: '#38bdf8',
  },
];

const basePath = process.env.NODE_ENV === 'production' ? '/oil-pipeline-portfolio' : '';

export default function ArchitectureDiagrams() {
  const [modal, setModal] = useState<Diagram | null>(null);

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
            Architecture
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            System Diagrams
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Six architecture diagrams generated with Mermaid CLI. Click any diagram to expand.
          </p>
        </motion.div>

        <motion.div
          variants={staggerContainerFast}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {diagrams.map((diagram) => (
            <motion.button
              key={diagram.key}
              variants={fadeUp}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              onClick={() => setModal(diagram)}
              className="group flex flex-col rounded-2xl overflow-hidden border border-white/5 bg-[#111827] hover:border-white/10 transition-all duration-300 text-left"
            >
              {/* Diagram thumbnail */}
              <div className="relative h-44 bg-[#080c12] overflow-hidden flex items-center justify-center">
                <Image
                  src={`${basePath}/diagrams/${diagram.key}.png`}
                  alt={diagram.title}
                  width={600}
                  height={300}
                  className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity duration-300 group-hover:scale-105 transition-transform"
                  unoptimized
                />
                {/* Expand hint */}
                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-black/40">
                  <div className="p-2 rounded-full bg-white/10 backdrop-blur-sm">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <h3
                  className="font-display text-base font-bold mb-1 group-hover:opacity-90 transition-colors"
                  style={{ color: diagram.accentColor }}
                >
                  {diagram.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">{diagram.description}</p>
              </div>
            </motion.button>
          ))}
        </motion.div>
      </div>

      {modal && (
        <DiagramModal
          src={`${basePath}/diagrams/${modal.key}.png`}
          alt={modal.title}
          onClose={() => setModal(null)}
        />
      )}
    </section>
  );
}
