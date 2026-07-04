import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import HeroSection from './HeroSection';
import StatsSection from './StatsSection';
import ModulesSection from './ModulesSection';
import RiskTeaserSection from './RiskTeaserSection';
import CTASection from './CTASection';
import './LandingPage.css';

gsap.registerPlugin(ScrollTrigger, useGSAP);

export default function LandingPage() {
  const containerRef = useRef(null);

  useGSAP(() => {
    // Global ScrollTrigger setup or smooth scrolling could go here if needed
  }, { scope: containerRef });

  return (
    <div className="landing-page" ref={containerRef}>
      <HeroSection />
      <StatsSection />
      <ModulesSection />
      <RiskTeaserSection />
      <CTASection />
    </div>
  );
}
