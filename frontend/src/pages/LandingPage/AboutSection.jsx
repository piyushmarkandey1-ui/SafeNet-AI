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
import ScrollStack, { ScrollStackItem } from '../../components/ui/ScrollStack';
import './AboutSection.css';

const FEATURES = [
// ... (features remain same, I'll keep the import at the top)
  {
    step: '01',
    icon: PhoneCall,
    title: 'Scam Call Detector',
    color: 'risk',
    where: 'Dashboard → "Scam Detector" pill or Risk Feed',
    guide: [
      'Open the Dashboard (click "Launch Dashboard" on the home page).',
      'Click the "Scam Detector" pill in the top nav — it scrolls to the Risk Feed.',
      'Hit "Simulate Scenario" (top-right) to inject a live scam-call event.',
      'Click any event card to see its AI threat score and detected tactics in the Evidence Panel.',
    ],
  },
  {
    step: '02',
    icon: ScanLine,
    title: 'Counterfeit Note Checker',
    color: 'warning',
    where: 'Home → "Try Note Checker"  or  Dashboard → "Note Checker" pill',
    guide: [
      'Click "Try Note Checker" on the home page, or click "Note Checker" in the Dashboard top nav.',
      'Upload a clear photo of any currency note (JPG / PNG).',
      'The AI analyses watermarks, serial numbers & printing micro-patterns.',
      'You receive a verdict — Genuine or Suspect — with a confidence score.',
    ],
  },
  {
    step: '03',
    icon: Network,
    title: 'Fraud Graph',
    color: 'trust',
    where: 'Dashboard → "Fraud Graph" pill → click any Risk Feed event',
    guide: [
      'Click the "Fraud Graph" pill in the Dashboard top nav to jump to the Risk Feed.',
      'Click any event card — the Evidence Panel slides in on the right.',
      'Nodes represent phone numbers, bank accounts & persons of interest.',
      'Edges show transaction flows; thicker lines mean higher suspicious activity.',
    ],
  },
  {
    step: '04',
    icon: Map,
    title: 'Geospatial Heatmap',
    color: 'risk',
    where: 'Dashboard → "Heatmap" pill or centre panel',
    guide: [
      'Click the "Heatmap" pill in the top nav — it scrolls to the live crime map.',
      'Red glowing circles = critical hotspots; teal = lower-risk clusters.',
      'Click any circle on the map to see the incident details in a popup.',
      'Simulate a new scenario to see hotspots update in real time.',
    ],
  },
  {
    step: '05',
    icon: Shield,
    title: 'Citizen Shield (AI Chat)',
    color: 'trust',
    where: 'Dashboard → "Citizen Shield" pill  or  chat bubble (bottom-right)',
    guide: [
      'Click the "Citizen Shield" pill in the top nav — the chat opens instantly.',
      'Or click the floating chat bubble at the bottom-right of the Dashboard.',
      'Type any question — e.g. "How do I avoid UPI scams?" or "Is this call a scam?"',
      'The RAG-powered AI responds with step-by-step prevention advice from RBI & MHA advisories.',
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

      gsap.from('.features-guide-carousel', {
        scrollTrigger: { trigger: '.features-guide-carousel', start: 'top 75%' },
        y: 50,
        opacity: 0,
        duration: 0.7,
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

        <div className="features-guide-carousel hide-scrollbar" style={{ height: '85vh', margin: '0 auto', maxWidth: '800px', overflow: 'hidden' }}>
          <ScrollStack itemDistance={150} itemScale={0.03} itemStackDistance={50} blurAmount={1.2} fadeAmount={0.7}>
            {FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <ScrollStackItem key={feat.step} itemClassName={`feature-card feature-card--${feat.color}`}>
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
                </ScrollStackItem>
              );
            })}
          </ScrollStack>
        </div>

      </div>
    </section>
  );
}
