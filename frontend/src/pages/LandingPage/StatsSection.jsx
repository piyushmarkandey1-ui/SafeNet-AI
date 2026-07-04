import { useRef } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import './StatsSection.css';

export default function StatsSection() {
  const sectionRef = useRef(null);

  useGSAP(() => {
    const mm = gsap.matchMedia();

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      // Fade in the text block
      gsap.from('.stats-intro', {
        scrollTrigger: {
          trigger: '.stats-intro',
          start: 'top 80%',
        },
        y: 30,
        opacity: 0,
        duration: 1,
        ease: 'power3.out'
      });

      // Animate the numbers counting up
      const counters = gsap.utils.toArray('.stat-number');
      counters.forEach((counter) => {
        const targetValue = parseFloat(counter.getAttribute('data-value'));
        
        gsap.to(counter, {
          scrollTrigger: {
            trigger: counter,
            start: 'top 85%',
          },
          innerHTML: targetValue,
          duration: 2,
          ease: 'power2.out',
          snap: { innerHTML: 0.1 }, // Snap to 1 decimal for millions
          onUpdate: function() {
            // Re-format to locale string for the 1,776 case
            if (targetValue > 1000) {
              counter.innerHTML = Math.round(this.targets()[0].innerHTML).toLocaleString('en-IN');
            }
          }
        });
      });

      // Fade up the stat blocks
      gsap.from('.stat-block', {
        scrollTrigger: {
          trigger: '.stats-grid',
          start: 'top 80%',
        },
        y: 40,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        stagger: 0.2
      });
    });
  }, { scope: sectionRef });

  return (
    <section className="landing-section stats-section" ref={sectionRef}>
      <div className="section-content stats-content">
        <div className="stats-intro">
          <h2>The scale of the threat is unprecedented.</h2>
          <p>Siloed tools fail to catch connected crime. We need a unified approach.</p>
        </div>

        <div className="stats-grid">
          <div className="stat-block">
            <div className="stat-value">
              <span className="stat-currency">₹</span>
              <span className="stat-number" data-value="1776">0</span>
              <span className="stat-suffix">cr</span>
            </div>
            <p className="stat-label">Lost to digital-arrest fraud in 2023</p>
          </div>
          
          <div className="stat-block">
            <div className="stat-value">
              <span className="stat-number" data-value="1.14">0</span>
              <span className="stat-suffix">m</span>
            </div>
            <p className="stat-label">Cybercrime complaints registered</p>
          </div>
        </div>
      </div>
    </section>
  );
}
