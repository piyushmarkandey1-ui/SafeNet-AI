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
import { useIsMobile } from '../../hooks/useIsMobile';
import './LandingPage.css';

gsap.registerPlugin(ScrollTrigger, useGSAP);

export default function LandingPage() {
  const containerRef = useRef(null);
  const isMobile = useIsMobile();

  useGSAP(() => {
    // Global ScrollTrigger setup or smooth scrolling could go here if needed
  }, { scope: containerRef });

  return (
    <div className="landing-page" ref={containerRef}>
      {isMobile && (
        <div className="mobile-experience-note">
          For the full interactive 3D experience, please open on a laptop or desktop.
        </div>
      )}
      <div className="landing-global-bg">
        {!isMobile && (
          <Galaxy 
            hueShift={190} /* Cyan/Teal to match --accent-trust */
            density={1.5}
            glowIntensity={0.6}
            saturation={0.8}
            starSpeed={0.8}
            mouseRepulsion={true}
            repulsionStrength={2.5}
          />
        )}
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
