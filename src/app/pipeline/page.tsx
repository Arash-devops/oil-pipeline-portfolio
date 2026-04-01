'use client';

import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';
import PipelineHero from '@/components/pipeline/PipelineHero';
import ArchitectureDiagrams from '@/components/pipeline/ArchitectureDiagrams';
import StageExplorer from '@/components/pipeline/StageExplorer';
import LiveDashboard from '@/components/pipeline/LiveDashboard';
import ApiExplorer from '@/components/pipeline/ApiExplorer';
import TechStackGrid from '@/components/pipeline/TechStackGrid';

export default function PipelinePage() {
  return (
    <main className="relative">
      <Navbar />
      <PipelineHero />
      <ArchitectureDiagrams />
      <StageExplorer />
      <LiveDashboard />
      <ApiExplorer />
      <TechStackGrid />
      <Footer />
    </main>
  );
}
