import { useRef } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import Galaxy from '../../components/ui/Galaxy';
import './CTASection.css';

export default function CTASection() {
  const sectionRef = useRef(null);

  useGSAP(() => {
    const mm = gsap.matchMedia();

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      gsap.from('.cta-content > *', {
        scrollTrigger: {
          trigger: '.cta-content',
          start: 'top 80%',
        },
        y: 30,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out'
      });
    });
  }, { scope: sectionRef });

  return (
    <section className="landing-section cta-section" ref={sectionRef}>
      <div className="cta-bg-canvas">
        <Galaxy 
          hueShift={190} /* Cyan/Teal to match --accent-trust */
          density={1.2}
          glowIntensity={0.6}
          saturation={0.8}
          starSpeed={0.8}
          mouseRepulsion={true}
          repulsionStrength={2.5}
        />
      </div>
      <div className="section-content cta-content">
        <h2>Ready to secure the digital frontier?</h2>
        <p>Explore the unified command center.</p>
        <Link to="/dashboard" className="cta-button">
          Launch Dashboard <ArrowRight size={18} />
        </Link>
      </div>
    </section>
  );
}
