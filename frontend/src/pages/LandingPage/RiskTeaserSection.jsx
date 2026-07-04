import { useRef } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import { GlassPanel } from '../../components/ui';
import './RiskTeaserSection.css';

export default function RiskTeaserSection() {
  const sectionRef = useRef(null);

  useGSAP(() => {
    const mm = gsap.matchMedia();

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: '.teaser-viz',
          start: 'top 70%',
        }
      });

      // Animate signals flowing in
      tl.from('.signal-dot', {
        scale: 0,
        opacity: 0,
        duration: 0.5,
        stagger: 0.2,
        ease: 'back.out(1.7)'
      })
      // Animate lines connecting
      .to('.signal-line', {
        width: '100%',
        duration: 0.6,
        stagger: 0.2,
        ease: 'power2.inOut'
      }, "-=0.6")
      // Animate score climbing
      .to('.teaser-score-value', {
        innerHTML: 94.2,
        duration: 1.5,
        ease: 'power3.out',
        snap: { innerHTML: 0.1 },
        onUpdate: function() {
          const val = this.targets()[0].innerHTML;
          if (val > 80) {
            gsap.to('.teaser-score-value', { color: 'var(--accent-risk)', duration: 0.2 });
            gsap.to('.teaser-core', { borderColor: 'var(--accent-risk)', boxShadow: '0 0 20px var(--accent-risk-glow)', duration: 0.2 });
          }
        }
      }, "-=0.4");
    });
  }, { scope: sectionRef });

  return (
    <section className="landing-section teaser-section" ref={sectionRef}>
      <div className="section-content">
        <div className="teaser-header">
          <h2>Compound Risk Detection</h2>
          <p>Individual signals might look benign. The orchestrator sees the full picture.</p>
        </div>

        <div className="teaser-viz">
          <div className="signals-column">
            <div className="signal-node"><span className="signal-dot"></span> IP Geolocation</div>
            <div className="signal-node"><span className="signal-dot"></span> Device Hash</div>
            <div className="signal-node"><span className="signal-dot"></span> Call Transcript</div>
          </div>
          
          <div className="connections-column">
             <div className="line-track"><div className="signal-line"></div></div>
             <div className="line-track"><div className="signal-line"></div></div>
             <div className="line-track"><div className="signal-line"></div></div>
          </div>

          <GlassPanel hoverable={false} className="teaser-core">
            <span className="teaser-score-label">Compound Score</span>
            <span className="teaser-score-value">12.0</span>
          </GlassPanel>
        </div>
      </div>
    </section>
  );
}
