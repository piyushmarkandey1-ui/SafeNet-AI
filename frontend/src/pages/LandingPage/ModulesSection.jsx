import { useRef } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import { PhoneCall, AlertTriangle, Network, Map, Shield } from 'lucide-react';
import { GlassPanel } from '../../components/ui';
import TiltedCard from '../../components/ui/TiltedCard';
import { useIsMobile } from '../../hooks/useIsMobile';
import './ModulesSection.css';

const MODULES = [
  { icon: PhoneCall, title: 'Scam Call Detection', desc: 'Real-time NLP transcript analysis to intercept vishing.' },
  { icon: AlertTriangle, title: 'Counterfeit Vision', desc: 'On-device neural networks flagging fake currency.' },
  { icon: Network, title: 'Fraud Graph', desc: 'Relational mapping to uncover hidden money mule rings.' },
  { icon: Map, title: 'Geospatial Heatmap', desc: 'Predictive geographic clustering of reported incidents.' },
  { icon: Shield, title: 'Citizen Shield', desc: 'RAG-powered conversational assistant for public prevention.' },
];

export default function ModulesSection() {
  const sectionRef = useRef(null);
  const isMobile = useIsMobile();

  useGSAP(() => {
    const mm = gsap.matchMedia();

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: '.modules-grid',
          start: 'top 75%',
        }
      });

      tl.from('.module-card-wrapper', {
        y: 50,
        opacity: 0,
        duration: 0.8,
        ease: 'power3.out',
        stagger: 0.15
      });

      // Animate a connecting line SVG
      gsap.from('.connection-line path', {
        scrollTrigger: {
          trigger: '.modules-grid',
          start: 'top 60%',
          end: 'bottom 40%',
          scrub: 1, // Tie drawing to scroll progress
        },
        strokeDashoffset: 1000,
        ease: 'none'
      });
    });
  }, { scope: sectionRef });

  return (
    <section className="landing-section modules-section" ref={sectionRef}>
      <div className="section-content">
        <div className="modules-header">
          <h2>Five Modules. One Orchestrator.</h2>
          <p>Each module specializes in a specific threat vector. The orchestrator ties them together.</p>
        </div>

        <div className="modules-grid">
          {/* SVG Connection Line (Abstract representation) */}
          <svg className="connection-line" viewBox="0 0 1000 200" preserveAspectRatio="none">
            <path 
              d="M 100 100 C 300 100, 300 50, 500 100 S 700 150, 900 100" 
              fill="none" 
              stroke="var(--accent-trust-dim)" 
              strokeWidth="2" 
              strokeDasharray="1000"
              strokeDashoffset="0"
            />
          </svg>

          {MODULES.map((mod, i) => {
            const Icon = mod.icon;
            
            if (isMobile) {
              return (
                <div key={i} className="module-card-wrapper">
                  <GlassPanel hoverable={false} className="module-card" style={{ height: '100%', pointerEvents: 'auto' }}>
                    <div className="module-icon-wrap">
                      <Icon size={24} />
                    </div>
                    <h3>{mod.title}</h3>
                    <p>{mod.desc}</p>
                  </GlassPanel>
                </div>
              );
            }

            return (
              <div key={i} className="module-card-wrapper">
                <TiltedCard
                  imageSrc={null}
                  containerHeight="auto"
                  containerWidth="100%"
                  imageHeight="auto"
                  imageWidth="100%"
                  rotateAmplitude={12}
                  scaleOnHover={1.05}
                  showMobileWarning={false}
                  showTooltip={false}
                  displayOverlayContent={true}
                  overlayContent={
                    <GlassPanel hoverable={false} className="module-card" style={{ height: '100%', pointerEvents: 'auto' }}>
                      <div className="module-icon-wrap">
                        <Icon size={24} />
                      </div>
                      <h3>{mod.title}</h3>
                      <p>{mod.desc}</p>
                    </GlassPanel>
                  }
                />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
