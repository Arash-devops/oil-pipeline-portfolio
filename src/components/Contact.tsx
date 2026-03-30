'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { fadeUp, slideInLeft, slideInRight, viewportOptions } from '@/lib/animations';
import { siteConfig } from '@/data/config';

const contactChannels = [
  {
    label: 'Email',
    value: siteConfig.email,
    href: siteConfig.social.email,
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    color: '#38bdf8',
  },
  {
    label: 'LinkedIn',
    value: 'linkedin.com/in/arashrazban',
    href: siteConfig.social.linkedin,
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
      </svg>
    ),
    color: '#818cf8',
  },
  {
    label: 'GitHub',
    value: 'github.com/arashrazban',
    href: siteConfig.social.github,
    icon: (
      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
        <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
      </svg>
    ),
    color: '#34d399',
  },
];

type FormState = 'idle' | 'sending' | 'success' | 'error';

export default function Contact() {
  const [formState, setFormState] = useState<FormState>('idle');
  const [formData, setFormData] = useState({ name: '', email: '', subject: '', message: '' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormState('sending');

    try {
      const res = await fetch('https://api.web3forms.com/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          access_key: 'YOUR_WEB3FORMS_ACCESS_KEY', // replace with your key
          ...formData,
        }),
      });
      const data = await res.json();
      if (data.success) {
        setFormState('success');
        setFormData({ name: '', email: '', subject: '', message: '' });
      } else {
        setFormState('error');
      }
    } catch {
      setFormState('error');
    }
  };

  const inputClass =
    'w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-400/50 focus:bg-white/8 transition-all duration-200';

  return (
    <section id="contact" className="relative py-24 lg:py-32 bg-[#0d1117]">
      <div className="section-divider absolute top-0 inset-x-0" />

      {/* Background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-radial from-cyan-400/5 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        {/* Header */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-16"
        >
          <p className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-3">
            06 / Contact
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Let&apos;s Connect
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Whether it&apos;s a job opportunity, a collaboration, or just a technical conversation — I&apos;d love to hear from you.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-start max-w-5xl mx-auto">
          {/* Left: Info */}
          <motion.div
            variants={slideInLeft}
            initial="hidden"
            whileInView="visible"
            viewport={viewportOptions}
            className="space-y-6"
          >
            <div>
              <h3 className="font-display text-2xl font-bold text-slate-100 mb-3">
                Open to opportunities
              </h3>
              <p className="text-slate-400 leading-relaxed">
                I&apos;m actively looking for roles in <span className="text-cyan-400">DevOps</span>,{' '}
                <span className="text-indigo-400">Data Engineering</span>, and{' '}
                <span className="text-green-400">Backend Development</span> — particularly in
                Germany and across Europe. Remote positions are welcome.
              </p>
            </div>

            <div className="space-y-3">
              {contactChannels.map((ch) => (
                <a
                  key={ch.label}
                  href={ch.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-4 p-4 rounded-xl border border-white/5 bg-white/3 hover:bg-white/6 hover:border-white/10 transition-all duration-200 group"
                >
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200"
                    style={{
                      color: ch.color,
                      backgroundColor: `${ch.color}15`,
                    }}
                  >
                    {ch.icon}
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 font-medium uppercase tracking-wide mb-0.5">
                      {ch.label}
                    </p>
                    <p className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors font-mono-custom">
                      {ch.value}
                    </p>
                  </div>
                  <svg className="w-4 h-4 text-slate-600 group-hover:text-slate-400 ml-auto transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </a>
              ))}
            </div>

            <div className="p-5 rounded-xl bg-cyan-400/5 border border-cyan-400/15">
              <p className="text-sm text-slate-400 leading-relaxed">
                <span className="text-cyan-400 font-semibold">Response time:</span> I typically
                reply within 24–48 hours. For urgent matters, LinkedIn is quickest.
              </p>
            </div>
          </motion.div>

          {/* Right: Form */}
          <motion.div
            variants={slideInRight}
            initial="hidden"
            whileInView="visible"
            viewport={viewportOptions}
          >
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-500 font-medium mb-1.5 uppercase tracking-wide">
                    Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Jane Smith"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className="block text-xs text-slate-500 font-medium mb-1.5 uppercase tracking-wide">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="jane@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className={inputClass}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs text-slate-500 font-medium mb-1.5 uppercase tracking-wide">
                  Subject
                </label>
                <input
                  type="text"
                  required
                  placeholder="Job opportunity / Collaboration / ..."
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                  className={inputClass}
                />
              </div>

              <div>
                <label className="block text-xs text-slate-500 font-medium mb-1.5 uppercase tracking-wide">
                  Message
                </label>
                <textarea
                  required
                  rows={5}
                  placeholder="Tell me about the role, project, or what's on your mind..."
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  className={`${inputClass} resize-none`}
                />
              </div>

              <button
                type="submit"
                disabled={formState === 'sending'}
                className="w-full py-3.5 px-6 bg-gradient-to-r from-cyan-500 to-indigo-500 text-white font-semibold text-sm rounded-xl hover:from-cyan-400 hover:to-indigo-400 disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-lg hover:shadow-cyan-500/20"
              >
                {formState === 'sending' ? 'Sending...' : 'Send Message'}
              </button>

              {formState === 'success' && (
                <motion.p
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-green-400 text-center font-medium"
                >
                  ✓ Message sent! I&apos;ll get back to you soon.
                </motion.p>
              )}
              {formState === 'error' && (
                <motion.p
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="text-sm text-rose-400 text-center font-medium"
                >
                  Something went wrong. Please try reaching out via email.
                </motion.p>
              )}
            </form>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
