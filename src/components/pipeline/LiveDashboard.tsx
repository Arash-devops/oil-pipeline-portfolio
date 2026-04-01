'use client';

import dynamic from 'next/dynamic';
import { motion } from 'framer-motion';
import { fadeUp, staggerContainerFast, viewportOptions } from '@/lib/animations';

// Dynamic imports prevent SSR errors with recharts
const PriceHistoryChart = dynamic(() => import('./PriceHistoryChart'), { ssr: false });
const CommodityComparisonChart = dynamic(() => import('./CommodityComparisonChart'), { ssr: false });
const MonthlySummaryChart = dynamic(() => import('./MonthlySummaryChart'), { ssr: false });
const SpreadChart = dynamic(() => import('./SpreadChart'), { ssr: false });

export default function LiveDashboard() {
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
            Live Dashboard
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Data Visualisation
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Charts connect to the live API when available, falling back to pre-computed sample data on this static site.
          </p>
        </motion.div>

        <motion.div
          variants={staggerContainerFast}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="grid md:grid-cols-2 gap-8"
        >
          {/* Price History */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl border border-white/5 bg-[#111827] p-6 flex flex-col"
            style={{ minHeight: 320 }}
          >
            <PriceHistoryChart />
          </motion.div>

          {/* WTI vs Brent */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl border border-white/5 bg-[#111827] p-6 flex flex-col"
            style={{ minHeight: 320 }}
          >
            <CommodityComparisonChart />
          </motion.div>

          {/* Monthly Returns */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl border border-white/5 bg-[#111827] p-6 flex flex-col"
            style={{ minHeight: 360 }}
          >
            <MonthlySummaryChart />
          </motion.div>

          {/* Spread */}
          <motion.div
            variants={fadeUp}
            className="rounded-2xl border border-white/5 bg-[#111827] p-6 flex flex-col"
            style={{ minHeight: 320 }}
          >
            <SpreadChart />
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
