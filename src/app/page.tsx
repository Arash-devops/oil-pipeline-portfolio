'use client';

import Navbar from '@/components/Navbar';
import Hero from '@/components/Hero';
import About from '@/components/About';
import SkillPillars from '@/components/SkillPillars';
import TechMarquee from '@/components/TechMarquee';
import Education from '@/components/Education';
import Projects from '@/components/Projects';
import Certifications from '@/components/Certifications';
import GeneralQuestions from '@/components/GeneralQuestions';
import Contact from '@/components/Contact';
import Footer from '@/components/Footer';

export default function Home() {
  return (
    <main className="relative">
      <Navbar />
      <Hero />
      <About />
      <SkillPillars />
      <TechMarquee />
      <Education />
      <Projects />
      <Certifications />
      <GeneralQuestions />
      <Contact />
      <Footer />
    </main>
  );
}
