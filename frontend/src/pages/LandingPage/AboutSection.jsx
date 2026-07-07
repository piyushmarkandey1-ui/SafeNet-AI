import { useRef } from 'react';
import { gsap } from 'gsap';
import { useGSAP } from '@gsap/react';
import { Link } from 'react-router-dom';
import {
  PhoneCall,
  ScanLine,
  Network,
  Map,
  Shield,
  ChevronRight,
} from 'lucide-react';
import './AboutSection.css';

const FEATURES = [
  {
    step: '01',
    icon: PhoneCall,
    title: 'Scam Call Detector',
    color: 'risk',
    where: 'Dashboard → Risk Feed',
    guide: [
      'Open the Dashboard from the home page.',
      'Click "Simulate Scenario" in the top-right to inject a live scam-call event.',
      'Select any event in the Risk Feed on the left to see its threat score.',
      'The Evidence Panel on the right shows entities, transcript snippets & graph links.',
    ],
  },
  {
    step: '02',
    icon: ScanLine,
    title: 'Counterfeit Note Checker',
    color: 'warning',
    where: 'Home → "Try Note Checker"',
    guide: [
      'Click the "Try Note Checker" button on the home page.',
      'Upload a photo of any currency note (JPG / PNG).',
      'The AI model analyses watermarks, serial numbers & printing patterns.',
      'A verdict — Genuine or Suspect — is returned with a confidence score.',
    ],
  },
  {
    step: '03',
    icon: Network,
    title: 'Fraud Graph',
    color: 'trust',
    where: 'Dashboard → click any event',
    guide: [
      'Open the Dashboard and click any event in the Risk Feed.',
      'The Evidence Panel loads a Fraud Graph showing connected entities.',
      'Nodes represent phone numbers, bank accounts, and persons of interest.',
      'Edges show transaction flows — thicker means more suspicious activity.',
    ],
  },
  {
    step: '04',
    icon: Map,
    title: 'Geospatial Heatmap',
    color: 'risk',
    where: 'Dashboard → Centre Map Panel',
    guide: [
      'The centre panel of the Dashboard always shows the live crime map.',
      'Hotspots glow red for high-risk zones and blue for low-risk zones.',
      'Clicking a map pin highlights the matching event in the Risk Feed.',
      'Hotspot data updates automatically when you simulate new scenarios.',
    ],
  },
  {
    step: '05',
    icon: Shield,
    title: 'Citizen Shield (AI Chat)',
    color: 'trust',
    where: 'Dashboard → Chat bubble (bottom-right)',
    guide: [
      'Open the Dashboard and click the floating chat bubble.',
      'Type any question — "How do I avoid UPI scams?" works great.',
      'Citizen Shield uses a RAG knowledge base of RBI & MHA advisories.',
      'It gives step-by-step prevention advice in plain language.',
    ],
  },
];

export default function AboutSection() {
  const sectionRef = useRef(null);

  useGSAP(() => {
    const mm = gsap.matchMedia();
    mm.add('(prefers-reduced-motion: no-preference)', () => {
      gsap.from('.about-intro > *', {
        scrollTrigger: { trigger: '.about-intro', start: 'top 80%' },
        y: 30,
        opacity: 0,
        duration: 0.8,
        stagger: 0.15,
        ease: 'power3.out',
      });

      gsap.from('.feature-card', {
        scrollTrigger: { trigger: '.features-guide', start: 'top 75%' },
        y: 50,
        opacity: 0,
        duration: 0.7,
        stagger: 0.12,
        ease: 'power3.out',
      });
    });
  }, { scope: sectionRef });

  return (
    <section className="landing-section about-section" ref={sectionRef} id="about">
      <div className="section-content">

        {/* ── Platform Overview ─────────────────────────── */}
        <div className="about-intro">
          <p className="section-eyebrow">What is SafeNet AI?</p>
          <h2 className="about-heading">
            India's unified AI layer<br />
            <span className="gradient-text">against digital crime.</span>
          </h2>
          <p className="about-body">
            SafeNet AI is a real-time threat-intelligence platform built for law
            enforcement officers and everyday citizens. It fuses five
            specialised AI modules — scam detection, counterfeit vision, fraud
            graphs, geospatial mapping and an advisory chatbot — under one
            command centre. Everything talks to a single orchestrator so that a
            phone scam flagged in Mumbai instantly surfaces related money-mule
            accounts on the fraud graph and lights up the heatmap.
          </p>
          <div className="about-cta-row">
            <Link to="/dashboard" className="about-launch-btn">
              Open Dashboard <ChevronRight size={16} />
            </Link>
            <span className="about-note">No login required · Runs on demo data</span>
          </div>
        </div>

        {/* ── User Guide ────────────────────────────────── */}
        <div className="guide-header">
          <p className="section-eyebrow">User Guide</p>
          <h3 className="guide-title">How to use each feature</h3>
        </div>

        <div className="features-guide">
          {FEATURES.map((feat) => {
            const Icon = feat.icon;
            return (
              <div key={feat.step} className={`feature-card feature-card--${feat.color}`}>
                <div className="feature-card__header">
                  <span className="feature-step">{feat.step}</span>
                  <div className={`feature-icon-wrap icon--${feat.color}`}>
                    <Icon size={20} />
                  </div>
                  <div className="feature-meta">
                    <h4 className="feature-title">{feat.title}</h4>
                    <span className="feature-where">{feat.where}</span>
                  </div>
                </div>
                <ol className="feature-steps">
                  {feat.guide.map((step, i) => (
                    <li key={i} className="feature-step-item">
                      <span className="step-num">{i + 1}</span>
                      <span>{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            );
          })}
        </div>

      </div>
    </section>
  );
}
