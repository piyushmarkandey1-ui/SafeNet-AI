import { useEffect, useRef } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';
import HeroSection from './HeroSection';
import StatsSection from './StatsSection';
import ModulesSection from './ModulesSection';
import AboutSection from './AboutSection';
import RiskTeaserSection from './RiskTeaserSection';
import CTASection from './CTASection';
import Galaxy from '../../components/ui/Galaxy';
import './LandingPage.css';

gsap.registerPlugin(ScrollTrigger, useGSAP);

export default function LandingPage() {
  const containerRef = useRef(null);

  useGSAP(() => {
    // Global ScrollTrigger setup or smooth scrolling could go here if needed
  }, { scope: containerRef });

  return (
    <div className="landing-page" ref={containerRef}>
      <div className="landing-global-bg">
        <Galaxy 
          hueShift={190} /* Cyan/Teal to match --accent-trust */
          density={1.5}
          glowIntensity={0.6}
          saturation={0.8}
          starSpeed={0.8}
          mouseRepulsion={true}
          repulsionStrength={2.5}
        />
      </div>
      <div className="landing-content">
        <HeroSection />
        <StatsSection />
      <ModulesSection />
      <AboutSection />
      <RiskTeaserSection />
      <CTASection />
      </div>
    </div>
  );
}
