'use client';

import { motion } from 'framer-motion';
import { heroStagger, fadeUp } from '@/lib/animations';

const stats = [
  { value: '3', label: "Master's Degrees" },
  { value: '4', label: 'Core Pillars' },
  { value: '40+', label: 'Technologies' },
];

const floatingBadges = [
  { label: 'Docker', color: '#38bdf8', delay: 0 },
  { label: 'Kubernetes', color: '#818cf8', delay: 0.8 },
  { label: 'Apache Spark', color: '#34d399', delay: 1.6 },
  { label: 'Terraform', color: '#fbbf24', delay: 0.4 },
  { label: 'Python', color: '#fb7185', delay: 1.2 },
  { label: 'PostgreSQL', color: '#38bdf8', delay: 2.0 },
  { label: 'Kafka', color: '#818cf8', delay: 0.6 },
  { label: 'FastAPI', color: '#34d399', delay: 1.4 },
];

export default function Hero() {
  const handleScroll = (href: string) => {
    const el = document.querySelector(href);
    if (el) {
      const top = el.getBoundingClientRect().top + window.scrollY - 72;
      window.scrollTo({ top, behavior: 'smooth' });
    }
  };

  return (
    <section
      id="hero"
      className="relative min-h-screen flex items-center overflow-hidden"
    >
      {/* Background glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-gradient-radial from-cyan-400/8 via-indigo-400/4 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-[600px] h-[400px] bg-gradient-radial from-indigo-400/6 to-transparent rounded-full blur-3xl" />
        <div className="absolute top-1/3 left-0 w-[400px] h-[300px] bg-gradient-radial from-green-400/5 to-transparent rounded-full blur-3xl" />
      </div>

      {/* Grid pattern */}
      <div
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(rgba(56,189,248,0.8) 1px, transparent 1px), linear-gradient(90deg, rgba(56,189,248,0.8) 1px, transparent 1px)`,
          backgroundSize: '60px 60px',
        }}
      />

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8 pt-32 pb-20 w-full">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          {/* Left: Text */}
          <motion.div
            variants={heroStagger}
            initial="hidden"
            animate="visible"
            className="flex flex-col"
          >
            {/* Greeting */}
            <motion.p
              variants={fadeUp}
              className="font-mono-custom text-sm font-medium text-cyan-400 mb-4 tracking-widest"
            >
              {'// Hello, I\'m'}
            </motion.p>

            {/* Name */}
            <motion.h1
              variants={fadeUp}
              className="font-display text-5xl sm:text-6xl lg:text-7xl font-black leading-none mb-6"
            >
              <span className="block text-slate-100">Arash</span>
              <span className="block text-gradient-cyan-indigo">Razban</span>
            </motion.h1>

            {/* Role */}
            <motion.div variants={fadeUp} className="mb-6">
              <p className="font-mono-custom text-base text-slate-400 tracking-wide">
                <span className="text-green-400">DevOps</span>
                <span className="text-slate-600 mx-2">/</span>
                <span className="text-indigo-400">Data Engineering</span>
                <span className="text-slate-600 mx-2">/</span>
                <span className="text-amber-400">Backend</span>
              </p>
            </motion.div>

            {/* Description */}
            <motion.p
              variants={fadeUp}
              className="text-base lg:text-lg text-slate-400 leading-relaxed max-w-lg mb-8 font-light"
            >
              Triple Master&apos;s graduate building resilient cloud infrastructure,
              scalable data pipelines, and high-performance backend systems.
              Based in Germany, open to exciting opportunities across Europe and beyond.
            </motion.p>

            {/* CTAs */}
            <motion.div variants={fadeUp} className="flex flex-wrap gap-4 mb-14">
              <button
                onClick={() => handleScroll('#skills')}
                className="group relative px-6 py-3 bg-gradient-to-r from-cyan-500 to-indigo-500 text-white font-semibold text-sm rounded-xl overflow-hidden transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/25 hover:scale-[1.02] active:scale-[0.98]"
              >
                <span className="relative z-10">Explore My Skills</span>
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </button>

              <button
                onClick={() => handleScroll('#contact')}
                className="px-6 py-3 text-sm font-semibold text-slate-200 border border-white/15 rounded-xl hover:bg-white/5 hover:border-white/25 transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
              >
                Get In Touch
              </button>
            </motion.div>

            {/* Stats */}
            <motion.div
              variants={fadeUp}
              className="flex flex-wrap gap-8"
            >
              {stats.map((stat) => (
                <div key={stat.label} className="text-center">
                  <p className="font-display text-3xl font-bold text-gradient-cyan-indigo mb-0.5">
                    {stat.value}
                  </p>
                  <p className="text-xs text-slate-500 font-medium tracking-wide uppercase">
                    {stat.label}
                  </p>
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* Right: Floating badges */}
          <div className="hidden lg:flex relative items-center justify-center h-[500px]">
            {/* Center glow ring */}
            <div className="absolute w-64 h-64 rounded-full border border-cyan-400/10 animate-[spin_20s_linear_infinite]" />
            <div className="absolute w-80 h-80 rounded-full border border-indigo-400/8 animate-[spin_30s_linear_infinite_reverse]" />
            <div className="absolute w-96 h-96 rounded-full border border-slate-700/30" />

            {/* Center icon */}
            <motion.div
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5, duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="relative z-10 w-24 h-24 rounded-2xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-white/10 flex items-center justify-center text-4xl shadow-2xl backdrop-blur-sm"
            >
              ⚡
            </motion.div>

            {/* Floating badges in orbit */}
            {floatingBadges.map((badge, i) => {
              const angle = (i / floatingBadges.length) * 360;
              const radius = 175;
              const x = Math.cos((angle * Math.PI) / 180) * radius;
              const y = Math.sin((angle * Math.PI) / 180) * radius;
              return (
                <div
                  key={badge.label}
                  style={{
                    position: 'absolute',
                    left: `calc(50% + ${x}px - 40px)`,
                    top: `calc(50% + ${y}px - 12px)`,
                  }}
                >
                  <motion.div
                    initial={{ opacity: 0, scale: 0 }}
                    animate={{ opacity: 1, scale: 1, y: [0, -8, 0] }}
                    transition={{
                      opacity: { delay: badge.delay + 0.8, duration: 0.4 },
                      scale: { delay: badge.delay + 0.8, duration: 0.4 },
                      y: {
                        delay: badge.delay,
                        duration: 3 + (i % 3) * 0.5,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      },
                    }}
                    className="px-3 py-1.5 rounded-full text-xs font-mono-custom font-semibold border backdrop-blur-sm whitespace-nowrap"
                    style={{
                      color: badge.color,
                      borderColor: `${badge.color}40`,
                      backgroundColor: `${badge.color}12`,
                    }}
                  >
                    {badge.label}
                  </motion.div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2, duration: 0.8 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-xs text-slate-600 font-mono-custom tracking-widest uppercase">scroll</span>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
            className="w-px h-8 bg-gradient-to-b from-slate-600 to-transparent"
          />
        </motion.div>
      </div>
    </section>
  );
}
