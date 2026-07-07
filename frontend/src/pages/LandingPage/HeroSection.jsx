import { useRef, useEffect } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import { Link } from 'react-router-dom';
import './HeroSection.css';

import Galaxy from '../../components/ui/Galaxy';

export default function HeroSection() {
  const sectionRef = useRef(null);

  useGSAP(() => {
    const mm = gsap.matchMedia();

    mm.add("(prefers-reduced-motion: no-preference)", () => {
      const tl = gsap.timeline();
      
      tl.from('.hero-eyebrow', {
        y: 20,
        opacity: 0,
        duration: 1,
        ease: 'power3.out',
        delay: 0.2
      })
      .from('.hero-title span', {
        y: 40,
        opacity: 0,
        duration: 1.2,
        ease: 'power3.out',
        stagger: 0.15
      }, "-=0.6")
      .from('.hero-subtitle', {
        y: 20,
        opacity: 0,
        duration: 1,
        ease: 'power3.out'
      }, "-=0.8")
      .from('.hero-actions', {
        y: 20,
        opacity: 0,
        duration: 1,
        ease: 'power3.out'
      }, "-=0.8");
    });
  }, { scope: sectionRef });

  return (
    <section className="landing-section hero-section" ref={sectionRef}>
      <div className="section-content hero-content">
        <p className="hero-eyebrow">SafeNet AI</p>
        <h1 className="hero-title">
          <span>One intelligence layer.</span>
          <br/>
          <span>Five threat surfaces.</span>
        </h1>
        <p className="hero-subtitle">
          The unified digital public safety platform designed for law enforcement and citizens.
        </p>
        
        <div className="hero-actions">
          <Link to="/dashboard" className="hero-btn primary-btn">
            Launch Dashboard
          </Link>
          <Link to="/note-checker" className="hero-btn secondary-btn">
            Try Note Checker
          </Link>
        </div>
      </div>
    </section>
  );
}
