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
import Hyperspeed from '../../components/ui/Hyperspeed';
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
        {isMobile ? (
          <Hyperspeed
            effectOptions={{
              distortion: 'turbulentDistortion',
              length: 400,
              roadWidth: 10,
              islandWidth: 2,
              lanesPerRoad: 3,
              fov: 90,
              fovSpeedUp: 150,
              speedUp: 2,
              carLightsFade: 0.4,
              totalSideLightSticks: 20,
              lightPairsPerRoadWay: 40,
              shoulderLinesWidthPercentage: 0.05,
              brokenLinesWidthPercentage: 0.1,
              brokenLinesLengthPercentage: 0.5,
              lightStickWidth: [0.12, 0.5],
              lightStickHeight: [1.3, 1.7],
              movingAwaySpeed: [60, 80],
              movingCloserSpeed: [-120, -160],
              carLightsLength: [12, 80],
              carLightsRadius: [0.05, 0.14],
              carWidthPercentage: [0.3, 0.5],
              carShiftX: [-0.8, 0.8],
              carFloorSeparation: [0, 5],
              colors: {
                roadColor: 0x080808,
                islandColor: 0x0a0a0a,
                background: 0x000000,
                shoulderLines: 0xffffff,
                brokenLines: 0xffffff,
                leftCars: [0xd856bf, 0x6750a2, 0xc247ac],
                rightCars: [0x03b3c3, 0x0e5ea5, 0x324555],
                sticks: 0x03b3c3
              }
            }}
          />
        ) : (
          <Galaxy 
            hueShift={190} /* Cyan/Teal to match --accent-trust */
            density={1.5}
            glowIntensity={0.6}
            saturation={0.8}
            starSpeed={0.8}
            mouseRepulsion={true}
            repulsionStrength={1.2}
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
