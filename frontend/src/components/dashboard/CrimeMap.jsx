import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { GlassPanel } from '../ui';
import './CrimeMap.css';

const SEVERITY = {
  CRITICAL: { color: '#f43f5e', glow: 'rgba(244,63,94,0.5)',  ring: 'rgba(244,63,94,0.18)', dotR: 7,  ringR: 16 },
  HIGH:     { color: '#fb923c', glow: 'rgba(251,146,60,0.4)',  ring: 'rgba(251,146,60,0.14)', dotR: 6,  ringR: 14 },
  MEDIUM:   { color: '#fbbf24', glow: 'rgba(251,191,36,0.35)', ring: 'rgba(251,191,36,0.12)', dotR: 5,  ringR: 12 },
  LOW:      { color: '#34d399', glow: 'rgba(52,211,153,0.3)',  ring: 'rgba(52,211,153,0.10)', dotR: 4,  ringR: 10 },
  SAFE:     { color: '#34d399', glow: 'rgba(52,211,153,0.3)',  ring: 'rgba(52,211,153,0.10)', dotR: 4,  ringR: 10 },
};

const USER_REPORT_SEV = { color: '#c084fc', glow: 'rgba(192,132,252,0.4)', dotR: 6, ringR: 14 };

const LEGEND_ITEMS = [
  { color: SEVERITY.CRITICAL.color, label: 'Critical' },
  { color: SEVERITY.HIGH.color,     label: 'High' },
  { color: SEVERITY.MEDIUM.color,   label: 'Medium' },
  { color: '#c084fc',               label: 'Citizen Report' },
];

function MapController({ selectedEvent }) {
  const map = useMap();
  useEffect(() => {
    if (selectedEvent?.location) {
      map.flyTo([selectedEvent.location.lat, selectedEvent.location.lng], 13, { duration: 1.5 });
    }
  }, [selectedEvent, map]);
  return null;
}

export function CrimeMap({ hotspots = [], loading, selectedEvent, userReports = [] }) {
  const center = [22.9734, 78.6569];
  const [legendExpanded, setLegendExpanded] = useState(false);

  return (
    <div className="crime-map-container">
      {/* Map title badge — top-left corner */}
      <div className="crime-map-badge">
        <span className="crime-map-badge__dot" />
        Live Threat Heatmap
      </div>
      
      {/* Loading Overlay */}
      {loading && (
        <div className="map-loading-overlay">
          <div className="map-spinner" />
          <span>Syncing grid data...</span>
        </div>
      )}

      <MapContainer
        center={center}
        zoom={5}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CARTO'
        />
        <MapController selectedEvent={selectedEvent} />

        {/* ── System hotspot markers ── */}
        {!loading && hotspots.map((spot) => {
          const s = SEVERITY[spot.type] || SEVERITY.MEDIUM;

          return (
            <React.Fragment key={spot.id}>
              {/* Outer soft ring */}
              <CircleMarker
                center={[spot.lat, spot.lng]}
                radius={s.ringR}
                pathOptions={{
                  color: s.color,
                  fillColor: s.color,
                  fillOpacity: 0.08,
                  weight: 1,
                  opacity: 0.3,
                }}
                interactive={false}
              />
              {/* Inner filled dot */}
              <CircleMarker
                center={[spot.lat, spot.lng]}
                radius={s.dotR}
                pathOptions={{
                  color: s.color,
                  fillColor: s.color,
                  fillOpacity: 1,
                  weight: 0,
                }}
                className={spot.type === 'CRITICAL' ? 'marker-pulse' : ''}
              >
                <Popup className="dark-popup">
                  <strong>{spot.label || spot.type}</strong>
                  <br />
                  <span style={{ color: s.color, fontWeight: 700 }}>{spot.type}</span>
                  &nbsp;·&nbsp;{(spot.intensity * 100).toFixed(0)}% intensity
                </Popup>
              </CircleMarker>
            </React.Fragment>
          );
        })}

        {/* ── Selected event pulse ── */}
        {selectedEvent?.location && (
          <CircleMarker
            center={[selectedEvent.location.lat, selectedEvent.location.lng]}
            radius={8}
            pathOptions={{ color: '#fff', fillColor: '#f43f5e', fillOpacity: 1, weight: 2 }}
            className="marker-pulse"
          >
            <Popup className="dark-popup">{selectedEvent.title}</Popup>
          </CircleMarker>
        )}

        {/* ── User-submitted citizen reports ── */}
        {userReports.map((report) => {
          if (!report?.location?.lat) return null;
          const s = USER_REPORT_SEV;
          return (
            <React.Fragment key={report.id}>
              <CircleMarker
                center={[report.location.lat, report.location.lng]}
                radius={s.ringR}
                pathOptions={{ color: s.color, fillColor: s.color, fillOpacity: 0.08, weight: 1, opacity: 0.35, dashArray: '3 3' }}
                interactive={false}
              />
              <CircleMarker
                center={[report.location.lat, report.location.lng]}
                radius={s.dotR}
                pathOptions={{ color: s.color, fillColor: s.color, fillOpacity: 1, weight: 0 }}
                className="marker-pulse"
              >
                <Popup className="dark-popup">
                  <strong>🚩 Citizen Report</strong>
                  <br />
                  <strong>{report.title}</strong>
                  <br />
                  📍 {report.location.name}
                  {report.landmark ? ` · ${report.landmark}` : ''}
                  <br />
                  <span style={{ color: SEVERITY[report.severity]?.color || s.color }}>
                    {report.severity}
                  </span>
                  <br />
                  {report.description?.substring(0, 100)}
                  {report.description?.length > 100 ? '…' : ''}
                </Popup>
              </CircleMarker>
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Legend — collapsible on mobile (tap to expand), always open on desktop */}
      <div className="crime-map-overlay">
        <GlassPanel
          hoverable={false}
          className={`map-legend${legendExpanded ? ' expanded' : ''}`}
        >
          <button 
            className="legend-title"
            onClick={() => setLegendExpanded(e => !e)}
            aria-expanded={legendExpanded}
            aria-controls="legend-items"
            style={{ 
              background: 'none', 
              border: 'none', 
              padding: 0, 
              width: '100%', 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              color: 'inherit',
              font: 'inherit',
              cursor: 'pointer'
            }}
          >
            Live Grid Status
            <span className="legend-toggle-arrow">
              {legendExpanded ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6"/></svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
              )}
            </span>
          </button>
          
          <div id="legend-items" className="legend-items-container">
            {LEGEND_ITEMS.map(({ color, label }) => (
              <div className="legend-item" key={label}>
                <span className="legend-dot" style={{ background: color, boxShadow: `0 0 6px ${color}` }} />
                {label}
              </div>
            ))}
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}
