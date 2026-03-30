'use client';

import { motion } from 'framer-motion';
import { fadeUp, staggerContainerFast, viewportOptions } from '@/lib/animations';

type Cert = {
  title: string;
  issuer: string;
  status: 'Planned' | 'In Progress' | 'Earned';
  icon: string;
  color: string;
  bg: string;
  border: string;
};

const certifications: Cert[] = [
  {
    title: 'AWS Solutions Architect',
    issuer: 'Amazon Web Services',
    status: 'Planned',
    icon: '☁️',
    color: '#fbbf24',
    bg: 'bg-amber-400/5',
    border: 'border-amber-400/15',
  },
  {
    title: 'Azure Data Engineer Associate',
    issuer: 'Microsoft',
    status: 'Planned',
    icon: '📊',
    color: '#818cf8',
    bg: 'bg-indigo-400/5',
    border: 'border-indigo-400/15',
  },
  {
    title: 'Certified Kubernetes Administrator',
    issuer: 'CNCF / Linux Foundation',
    status: 'Planned',
    icon: '⎈',
    color: '#38bdf8',
    bg: 'bg-cyan-400/5',
    border: 'border-cyan-400/15',
  },
  {
    title: 'HashiCorp Terraform Associate',
    issuer: 'HashiCorp',
    status: 'Planned',
    icon: '🏗️',
    color: '#34d399',
    bg: 'bg-green-400/5',
    border: 'border-green-400/15',
  },
  {
    title: 'CompTIA Security+',
    issuer: 'CompTIA',
    status: 'Planned',
    icon: '🔒',
    color: '#fb7185',
    bg: 'bg-rose-400/5',
    border: 'border-rose-400/15',
  },
];

export default function Certifications() {
  return (
    <section id="certifications" className="relative py-24 lg:py-32">
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
            05 / Certifications
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Certification Roadmap
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Planned certifications to formalise and validate expertise across cloud,
            infrastructure, and security domains.
          </p>
        </motion.div>

        {/* Grid */}
        <motion.div
          variants={staggerContainerFast}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 max-w-4xl mx-auto"
        >
          {certifications.map((cert) => (
            <motion.div
              key={cert.title}
              variants={fadeUp}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className={`group relative p-6 rounded-2xl ${cert.bg} border ${cert.border} hover:border-opacity-40 transition-all duration-300`}
            >
              {/* Status badge */}
              <div className="flex items-center justify-between mb-5">
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                  style={{ backgroundColor: `${cert.color}15` }}
                >
                  {cert.icon}
                </div>
                <span
                  className="px-2.5 py-1 rounded-full text-xs font-mono-custom font-semibold border"
                  style={{
                    color: cert.color,
                    borderColor: `${cert.color}40`,
                    backgroundColor: `${cert.color}10`,
                  }}
                >
                  {cert.status}
                </span>
              </div>

              <h3 className="font-display text-base font-semibold text-slate-100 mb-1.5 leading-snug">
                {cert.title}
              </h3>
              <p className="text-xs text-slate-500">
                {cert.issuer}
              </p>

              {/* Progress bar (empty for Planned) */}
              <div className="mt-4 h-1 bg-white/5 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full opacity-40"
                  style={{
                    width: cert.status === 'Earned' ? '100%' : cert.status === 'In Progress' ? '50%' : '0%',
                    backgroundColor: cert.color,
                  }}
                />
              </div>
              <p className="mt-1.5 text-xs text-slate-600 font-mono-custom">
                {cert.status === 'Planned' ? 'Not started' : cert.status === 'In Progress' ? '~50% ready' : 'Complete'}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
