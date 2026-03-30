'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeUp, viewportOptions } from '@/lib/animations';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

const SUGGESTED_QUESTIONS = [
  'What is your tech stack?',
  'Are you open to remote work?',
  'What are your strongest skills?',
  'Tell me about your experience.',
];

const SYSTEM_PROMPT = `You are a helpful assistant representing Arash Razban's portfolio website. Answer questions about Arash concisely and professionally.

About Arash:
- DevOps Engineer, Data Engineer, and Backend Developer based in Germany
- Holds triple Master's degrees
- Passionate about cloud infrastructure, data pipelines, and building reliable systems at scale
- Actively seeking roles in DevOps, Data Engineering, and Backend Development in Germany and across Europe — remote positions welcome
- Contact: arash.razban@example.com | linkedin.com/in/arashrazban | github.com/arashrazban
- Tech stack includes: Docker, Kubernetes, CI/CD pipelines, Python, SQL, cloud platforms (AWS/GCP/Azure), data engineering tools
- Typically replies within 24–48 hours; LinkedIn is fastest for urgent matters

Keep responses friendly, concise, and accurate. If asked something you don't know about Arash, suggest they reach out directly via the contact form or LinkedIn.`;

export default function GeneralQuestions() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    const userMessage: Message = { role: 'user', content: trimmed };
    const updatedMessages = [...messages, userMessage];
    setMessages(updatedMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          system: SYSTEM_PROMPT,
          messages: updatedMessages,
        }),
      });

      const data = await response.json();
      const reply = data.content?.[0]?.text ?? "Sorry, I couldn't generate a response.";
      setMessages((prev) => [...prev, { role: 'assistant', content: reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Something went wrong. Please try again or reach out via the contact form.' },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <section id="general-questions" className="relative py-24 lg:py-32 bg-[#0a0e17]">
      <div className="section-divider absolute top-0 inset-x-0" />

      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-radial from-indigo-400/5 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-12"
        >
          <p className="font-mono-custom text-xs text-indigo-400 tracking-[0.2em] uppercase mb-3">
            06 / General Questions
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            Ask Me Anything
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            Have a quick question about my background, skills, or availability?
            Ask below — powered by AI, answered instantly.
          </p>
        </motion.div>

        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="max-w-3xl mx-auto"
        >
          <div className="rounded-2xl border border-white/8 bg-[#111827]/60 backdrop-blur-md overflow-hidden shadow-2xl">
            <div className="flex items-center gap-3 px-5 py-4 border-b border-white/5 bg-white/2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-rose-400/60" />
                <div className="w-3 h-3 rounded-full bg-amber-400/60" />
                <div className="w-3 h-3 rounded-full bg-green-400/60" />
              </div>
              <div className="flex items-center gap-2 ml-1">
                <div className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
                <span className="font-mono-custom text-xs text-slate-400 tracking-wide">
                  general-questions — AI assistant
                </span>
              </div>
            </div>

            <div className="h-80 overflow-y-auto px-5 py-5 space-y-4 scroll-smooth">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
                  <div className="w-12 h-12 rounded-xl bg-indigo-400/10 border border-indigo-400/20 flex items-center justify-center">
                    <svg className="w-6 h-6 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                  </div>
                  <p className="text-slate-500 text-sm">Start by asking a question or pick a suggestion below.</p>
                </div>
              )}

              <AnimatePresence initial={false}>
                {messages.map((msg, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-7 h-7 rounded-lg bg-indigo-400/15 border border-indigo-400/20 flex items-center justify-center flex-shrink-0 mr-2.5 mt-0.5">
                        <svg className="w-3.5 h-3.5 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2a10 10 0 110 20A10 10 0 0112 2zm0 2a8 8 0 100 16A8 8 0 0012 4zm-1 11h2v2h-2v-2zm0-8h2v6h-2V7z"/>
                        </svg>
                      </div>
                    )}
                    <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-cyan-400/20 text-slate-200 rounded-tr-sm'
                        : 'bg-white/4 border border-white/6 text-slate-300 rounded-tl-sm'
                    }`}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {isLoading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start"
                >
                  <div className="w-7 h-7 rounded-lg bg-indigo-400/15 border border-indigo-400/20 flex items-center justify-center flex-shrink-0 mr-2.5 mt-0.5">
                    <svg className="w-3.5 h-3.5 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2a10 10 0 110 20A10 10 0 0112 2zm0 2a8 8 0 100 16A8 8 0 0012 4zm-1 11h2v2h-2v-2zm0-8h2v6h-2V7z"/>
                    </svg>
                  </div>
                  <div className="px-4 py-3 rounded-2xl rounded-tl-sm bg-white/4 border border-white/6 flex items-center gap-1.5">
                    {[0, 1, 2].map((i) => (
                      <span key={i} className="w-1.5 h-1.5 rounded-full bg-indigo-400/60 animate-bounce"
                        style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                </motion.div>
              )}
              <div ref={bottomRef} />
            </div>

            {messages.length === 0 && (
              <div className="px-5 pb-4 flex flex-wrap gap-2">
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button key={q} onClick={() => sendMessage(q)}
                    className="font-mono-custom text-xs px-3 py-1.5 rounded-lg border border-indigo-400/20 text-indigo-300 bg-indigo-400/5 hover:bg-indigo-400/10 hover:border-indigo-400/30 transition-all duration-200">
                    {q}
                  </button>
                ))}
              </div>
            )}

            <div className="px-5 pb-5">
              <form onSubmit={handleSubmit} className="flex items-center gap-3">
                <input ref={inputRef} type="text" value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask a question about Arash..."
                  className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-400/50 focus:bg-white/8 transition-all duration-200 font-mono-custom"
                  disabled={isLoading} />
                <button type="submit" disabled={isLoading || !input.trim()}
                  className="w-11 h-11 flex-shrink-0 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white hover:from-indigo-400 hover:to-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-lg hover:shadow-indigo-500/20">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                </button>
              </form>
            </div>
          </div>

          <p className="text-center text-xs text-slate-600 mt-4 font-mono-custom">
            Responses are AI-generated based on Arash&apos;s profile · For detailed inquiries use the{' '}
            <a href="#contact" className="text-indigo-400/70 hover:text-indigo-400 transition-colors">
              contact form
            </a>
          </p>
        </motion.div>
      </div>
    </section>
  );
}