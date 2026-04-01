'use client';

import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Image from 'next/image';

type DiagramModalProps = {
  src: string;
  alt: string;
  onClose: () => void;
};

export default function DiagramModal({ src, alt, onClose }: DiagramModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
          className="relative max-w-5xl w-full rounded-2xl overflow-hidden border border-white/10 bg-[#0d1117] shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-white/5">
            <span className="text-sm text-slate-400 font-mono-custom">{alt}</span>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-white/8 text-slate-400 hover:text-slate-100 transition-colors"
              aria-label="Close"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Image */}
          <div className="p-4 flex items-center justify-center bg-[#080c12]">
            <Image
              src={src}
              alt={alt}
              width={1400}
              height={700}
              className="max-h-[75vh] w-auto object-contain rounded-lg"
              unoptimized
            />
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
