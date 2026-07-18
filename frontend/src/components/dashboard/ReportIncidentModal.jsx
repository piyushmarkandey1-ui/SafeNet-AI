import React, { useState } from 'react';
import { X, MapPin, AlertTriangle, Send, CheckCircle, Loader } from 'lucide-react';
import './ReportIncidentModal.css';

const INCIDENT_TYPES = [
  { value: 'UPI_FRAUD',        label: '💸 UPI / Payment Fraud' },
  { value: 'SCAM_CALL',        label: '📞 Scam / Phishing Call' },
  { value: 'COUNTERFEIT_NOTE', label: '💵 Counterfeit Currency' },
  { value: 'ONLINE_SCAM',      label: '🌐 Online / Social Media Scam' },
  { value: 'ROBBERY',          label: '🔪 Robbery / Theft' },
  { value: 'ASSAULT',          label: '⚠️ Assault / Physical Crime' },
  { value: 'IDENTITY_THEFT',   label: '🪪 Identity / Aadhaar Fraud' },
  { value: 'OTHER',            label: '🚨 Other Incident' },
];

const SEVERITY_OPTIONS = [
  { value: 'LOW',      label: 'Low',      color: '#2ec4b6', desc: 'Minor, no immediate danger' },
  { value: 'MEDIUM',   label: 'Medium',   color: '#f59e0b', desc: 'Concerning, needs attention' },
  { value: 'HIGH',     label: 'High',     color: '#ff6b35', desc: 'Serious, act quickly' },
  { value: 'CRITICAL', label: 'Critical', color: '#ff3b3b', desc: 'Extreme danger / ongoing' },
];

const INDIAN_CITIES = [
  { name: 'New Delhi',   lat: 28.6139, lng: 77.2090 },
  { name: 'Mumbai',      lat: 19.0760, lng: 72.8777 },
  { name: 'Bengaluru',   lat: 12.9716, lng: 77.5946 },
  { name: 'Kolkata',     lat: 22.5726, lng: 88.3639 },
  { name: 'Hyderabad',   lat: 17.3850, lng: 78.4867 },
  { name: 'Ahmedabad',   lat: 23.0225, lng: 72.5714 },
  { name: 'Lucknow',     lat: 26.8467, lng: 80.9462 },
  { name: 'Chennai',     lat: 13.0827, lng: 80.2707 },
  { name: 'Pune',        lat: 18.5204, lng: 73.8567 },
  { name: 'Jaipur',      lat: 26.9124, lng: 75.7873 },
  { name: 'Surat',       lat: 21.1702, lng: 72.8311 },
  { name: 'Kanpur',      lat: 26.4499, lng: 80.3319 },
  { name: 'Nagpur',      lat: 21.1458, lng: 79.0882 },
  { name: 'Indore',      lat: 22.7196, lng: 75.8577 },
  { name: 'Bhopal',      lat: 23.2599, lng: 77.4126 },
  { name: 'Patna',       lat: 25.5941, lng: 85.1376 },
  { name: 'Vadodara',    lat: 22.3072, lng: 73.1812 },
  { name: 'Ghaziabad',   lat: 28.6692, lng: 77.4538 },
  { name: 'Ludhiana',    lat: 30.9010, lng: 75.8573 },
  { name: 'Agra',        lat: 27.1767, lng: 78.0081 },
  { name: 'Nashik',      lat: 19.9975, lng: 73.7898 },
  { name: 'Meerut',      lat: 28.9845, lng: 77.7064 },
  { name: 'Rajkot',      lat: 22.3039, lng: 70.8022 },
  { name: 'Varanasi',    lat: 25.3176, lng: 82.9739 },
  { name: 'Coimbatore',  lat: 11.0168, lng: 76.9558 },
  { name: 'Kochi',       lat: 9.9312,  lng: 76.2673 },
  { name: 'Visakhapatnam', lat: 17.6868, lng: 83.2185 },
  { name: 'Chandigarh',  lat: 30.7333, lng: 76.7794 },
  { name: 'Guwahati',    lat: 26.1445, lng: 91.7362 },
  { name: 'Bhubaneswar', lat: 20.2961, lng: 85.8245 },
];

const INITIAL_FORM = {
  type: '',
  severity: 'MEDIUM',
  title: '',
  description: '',
  city: '',
  landmark: '',
  contactName: '',
  contactPhone: '',
};

export default function ReportIncidentModal({ onClose, onSubmit }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [step, setStep] = useState(1); // 1 = details, 2 = location, 3 = done
  const [submitting, setSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const set = (field, value) => {
    setForm(f => ({ ...f, [field]: value }));
    setErrors(e => ({ ...e, [field]: undefined }));
  };

  const validateStep1 = () => {
    const e = {};
    if (!form.type) e.type = 'Please select an incident type';
    if (!form.title.trim()) e.title = 'Please give a brief title';
    if (!form.description.trim() || form.description.trim().length < 20)
      e.description = 'Please describe the incident (at least 20 characters)';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const validateStep2 = () => {
    const e = {};
    if (!form.city) e.city = 'Please select your city / area';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleNext = () => {
    if (step === 1 && validateStep1()) setStep(2);
  };

  const handleSubmit = async () => {
    if (!validateStep2()) return;
    setSubmitting(true);
    const cityData = INDIAN_CITIES.find(c => c.name === form.city);
    // Small random offset so overlapping city reports don't stack exactly
    const jitter = () => (Math.random() - 0.5) * 0.05;
    const report = {
      id: `user-report-${Date.now()}`,
      type: form.type,
      severity: form.severity,
      title: form.title,
      description: form.description,
      landmark: form.landmark,
      contactName: form.contactName,
      contactPhone: form.contactPhone,
      city: form.city,
      location: {
        lat: (cityData?.lat ?? 22.97) + jitter(),
        lng: (cityData?.lng ?? 78.66) + jitter(),
        name: form.city,
      },
      timestamp: new Date().toISOString(),
      score: form.severity === 'CRITICAL' ? 95 : form.severity === 'HIGH' ? 78 : form.severity === 'MEDIUM' ? 55 : 30,
      isUserReport: true,
      entities: form.contactPhone ? [form.contactPhone] : [],
    };
    await new Promise(r => setTimeout(r, 900)); // smooth UX delay
    setSubmitting(false);
    setStep(3);
    onSubmit(report);
  };

  const selectedSeverity = SEVERITY_OPTIONS.find(s => s.value === form.severity);

  return (
    <div className="rim-backdrop" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="rim-modal">

        {/* Header */}
        <div className="rim-header">
          <div className="rim-header__left">
            <AlertTriangle size={20} className="rim-header__icon" />
            <div>
              <h2 className="rim-header__title">Report an Incident</h2>
              <p className="rim-header__sub">Your report helps protect your community</p>
            </div>
          </div>
          <button className="rim-close" onClick={onClose}><X size={18} /></button>
        </div>

        {/* Step bar */}
        {step < 3 && (
          <div className="rim-steps">
            <div className={`rim-step ${step >= 1 ? 'active' : ''}`}>
              <span className="rim-step__num">1</span>
              <span className="rim-step__label">Incident Details</span>
            </div>
            <div className="rim-step__line" />
            <div className={`rim-step ${step >= 2 ? 'active' : ''}`}>
              <span className="rim-step__num">2</span>
              <span className="rim-step__label">Location</span>
            </div>
          </div>
        )}

        {/* ── STEP 1: Incident Details ── */}
        {step === 1 && (
          <div className="rim-body">
            {/* Incident Type */}
            <div className="rim-field">
              <label className="rim-label">Incident Type <span className="rim-required">*</span></label>
              <div className="rim-type-grid">
                {INCIDENT_TYPES.map(t => (
                  <button
                    key={t.value}
                    type="button"
                    className={`rim-type-btn ${form.type === t.value ? 'selected' : ''}`}
                    onClick={() => set('type', t.value)}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              {errors.type && <span className="rim-error">{errors.type}</span>}
            </div>

            {/* Severity */}
            <div className="rim-field">
              <label className="rim-label">Severity Level</label>
              <div className="rim-severity-row">
                {SEVERITY_OPTIONS.map(s => (
                  <button
                    key={s.value}
                    type="button"
                    className={`rim-severity-btn ${form.severity === s.value ? 'selected' : ''}`}
                    style={{ '--sev-color': s.color }}
                    onClick={() => set('severity', s.value)}
                  >
                    <span className="rim-sev-dot" />
                    <span className="rim-sev-label">{s.label}</span>
                  </button>
                ))}
              </div>
              {selectedSeverity && (
                <p className="rim-hint">{selectedSeverity.desc}</p>
              )}
            </div>

            {/* Title */}
            <div className="rim-field">
              <label className="rim-label">Brief Title <span className="rim-required">*</span></label>
              <input
                className={`rim-input ${errors.title ? 'error' : ''}`}
                placeholder="e.g. Received fake ₹500 note at market"
                value={form.title}
                onChange={e => set('title', e.target.value)}
                maxLength={100}
              />
              {errors.title && <span className="rim-error">{errors.title}</span>}
            </div>

            {/* Description */}
            <div className="rim-field">
              <label className="rim-label">What Happened? <span className="rim-required">*</span></label>
              <textarea
                className={`rim-textarea ${errors.description ? 'error' : ''}`}
                placeholder="Describe the incident in detail — what happened, who was involved, what was said or done, any suspicious numbers or accounts..."
                value={form.description}
                onChange={e => set('description', e.target.value)}
                rows={4}
              />
              <span className="rim-char-count">{form.description.length}/1000</span>
              {errors.description && <span className="rim-error">{errors.description}</span>}
            </div>

            <div className="rim-footer">
              <button className="rim-btn-secondary" onClick={onClose}>Cancel</button>
              <button className="rim-btn-primary" onClick={handleNext}>
                Next: Location →
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 2: Location + Contact ── */}
        {step === 2 && (
          <div className="rim-body">
            <div className="rim-field">
              <label className="rim-label">
                <MapPin size={14} style={{ display: 'inline', marginRight: 4 }} />
                City / Area <span className="rim-required">*</span>
              </label>
              <input
                list="indian-cities"
                className={`rim-input ${errors.city ? 'error' : ''}`}
                placeholder="Type or select a city..."
                value={form.city}
                onChange={e => set('city', e.target.value)}
                autoComplete="off"
              />
              <datalist id="indian-cities">
                {INDIAN_CITIES.map(c => (
                  <option key={c.name} value={c.name}>{c.name}</option>
                ))}
              </datalist>
              {errors.city && <span className="rim-error">{errors.city}</span>}
            </div>

            <div className="rim-field">
              <label className="rim-label">Landmark / Locality (optional)</label>
              <input
                className="rim-input"
                placeholder="e.g. Near Connaught Place, Sector 12 Market..."
                value={form.landmark}
                onChange={e => set('landmark', e.target.value)}
              />
            </div>

            <div className="rim-divider">Your Contact (optional — kept private)</div>

            <div className="rim-field-row">
              <div className="rim-field">
                <label className="rim-label">Your Name</label>
                <input
                  className="rim-input"
                  placeholder="Anonymous"
                  value={form.contactName}
                  onChange={e => set('contactName', e.target.value)}
                />
              </div>
              <div className="rim-field">
                <label className="rim-label">Phone Number</label>
                <input
                  className="rim-input"
                  placeholder="+91 XXXXX XXXXX"
                  value={form.contactPhone}
                  onChange={e => set('contactPhone', e.target.value)}
                />
              </div>
            </div>

            <div className="rim-privacy-note">
              🔒 Your contact info is never shown publicly. It helps authorities follow up.
            </div>

            <div className="rim-footer">
              <button className="rim-btn-secondary" onClick={() => setStep(1)}>← Back</button>
              <button
                className="rim-btn-primary rim-btn-submit"
                onClick={handleSubmit}
                disabled={submitting}
              >
                {submitting
                  ? <><Loader size={15} className="animate-spin" /> Submitting…</>
                  : <><Send size={15} /> Submit Report</>
                }
              </button>
            </div>
          </div>
        )}

        {/* ── STEP 3: Success ── */}
        {step === 3 && (
          <div className="rim-body rim-success">
            <div className="rim-success__icon-wrap">
              <CheckCircle size={56} className="rim-success__icon" />
            </div>
            <h3 className="rim-success__title">Report Submitted!</h3>
            <p className="rim-success__msg">
              Your incident has been added to the SafeNet AI crime map and the live risk feed. 
              Authorities in your area will be alerted automatically.
            </p>
            <div className="rim-success__detail">
              <span className="rim-success__city">📍 {form.city}</span>
              <span className="rim-success__type">{INCIDENT_TYPES.find(t => t.value === form.type)?.label}</span>
            </div>
            <button className="rim-btn-primary" onClick={onClose}>
              Close &amp; View on Map
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
