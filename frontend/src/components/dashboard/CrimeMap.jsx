import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Circle, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { GlassPanel } from '../ui';
import './CrimeMap.css';

const SEVERITY_COLORS = {
  CRITICAL: '#ff3b3b',
  HIGH:     '#ff6b35',
  MEDIUM:   '#f59e0b',
  LOW:      '#2ec4b6',
  SAFE:     '#2ec4b6',
};

const SEVERITY_FILL_OPACITY = {
  CRITICAL: 0.18,
  HIGH:     0.14,
  MEDIUM:   0.10,
  LOW:      0.07,
  SAFE:     0.07,
};

// Component to dynamically re-center map if selected event changes
function MapController({ selectedEvent }) {
  const map = useMap();
  useEffect(() => {
    if (selectedEvent?.location) {
      map.flyTo([selectedEvent.location.lat, selectedEvent.location.lng], 13, {
        duration: 1.5,
      });
    }
  }, [selectedEvent, map]);
  return null;
}

export function CrimeMap({ hotspots = [], loading, selectedEvent, userReports = [] }) {
  // Default center: India
  const center = [22.9734, 78.6569];

  return (
    <div className="crime-map-container">
      <MapContainer 
        center={center} 
        zoom={5}
        style={{ height: '100%', width: '100%', background: 'var(--bg-base)' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
        />
        
        <MapController selectedEvent={selectedEvent} />

        {!loading && hotspots.map((spot) => {
          const color = SEVERITY_COLORS[spot.type] || SEVERITY_COLORS.MEDIUM;
          const fillOp = SEVERITY_FILL_OPACITY[spot.type] ?? 0.10;
          const dotRadius = 6 + spot.intensity * 18;
          const ringRadius = spot.radius ? spot.radius * 80 : spot.intensity * 80000;

          return (
            <React.Fragment key={spot.id}>
              {/* Big translucent alert zone ring */}
              <Circle
                center={[spot.lat, spot.lng]}
                radius={ringRadius}
                pathOptions={{
                  color,
                  fillColor: color,
                  fillOpacity: fillOp,
                  weight: 1.5,
                  dashArray: spot.type === 'CRITICAL' ? '6 4' : undefined,
                }}
              />

              {/* Centre dot marker */}
              <CircleMarker
                center={[spot.lat, spot.lng]}
                pathOptions={{
                  color: '#fff',
                  fillColor: color,
                  fillOpacity: 0.95,
                  weight: 2,
                }}
                radius={dotRadius}
                className={spot.type === 'CRITICAL' ? 'breathing-marker' : ''}
              >
                <Popup className="dark-popup">
                  <strong>{spot.label || spot.type} Alert Zone</strong><br/>
                  Severity: <span style={{ color }}>{spot.type}</span><br/>
                  Intensity: {(spot.intensity * 100).toFixed(0)}%
                </Popup>
              </CircleMarker>
            </React.Fragment>
          );
        })}

        {selectedEvent?.location && (
          <CircleMarker
            center={[selectedEvent.location.lat, selectedEvent.location.lng]}
            pathOptions={{
              color: '#fff',
              fillColor: '#ff3b3b',
              fillOpacity: 1,
              weight: 2,
            }}
            radius={8}
            className="pulse-marker"
          >
            <Popup className="dark-popup">{selectedEvent.title}</Popup>
          </CircleMarker>
        )}

        {/* User-submitted reports — distinct purple markers */}
        {userReports.map((report) => {
          if (!report?.location?.lat) return null;
          const repColor = '#a855f7';
          const sevColor = SEVERITY_COLORS[report.severity] || repColor;
          return (
            <React.Fragment key={report.id}>
              <Circle
                center={[report.location.lat, report.location.lng]}
                radius={40000}
                pathOptions={{
                  color: repColor,
                  fillColor: repColor,
                  fillOpacity: 0.12,
                  weight: 1.5,
                  dashArray: '4 4',
                }}
              />
              <CircleMarker
                center={[report.location.lat, report.location.lng]}
                pathOptions={{
                  color: '#fff',
                  fillColor: repColor,
                  fillOpacity: 0.95,
                  weight: 2,
                }}
                radius={10}
                className="pulse-marker"
              >
                <Popup className="dark-popup">
                  <strong>🚩 Citizen Report</strong><br/>
                  <strong>{report.title}</strong><br/>
                  📍 {report.location.name}{report.landmark ? ` · ${report.landmark}` : ''}<br/>
                  Severity: <span style={{ color: sevColor }}>{report.severity}</span><br/>
                  {report.description?.substring(0, 120)}{report.description?.length > 120 ? '…' : ''}
                </Popup>
              </CircleMarker>
            </React.Fragment>
          );
        })}
      </MapContainer>
      
      {/* Overlay Legend */}
      <div className="crime-map-overlay">
         <GlassPanel hoverable={false} className="map-legend">
            <span className="legend-title">Live Grid Status</span>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: SEVERITY_COLORS.CRITICAL }}></span>
              Critical Hotspot
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: SEVERITY_COLORS.HIGH }}></span>
              High Activity
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: SEVERITY_COLORS.MEDIUM }}></span>
              Elevated Activity
            </div>
            <div className="legend-item">
              <span className="legend-dot" style={{ background: '#a855f7' }}></span>
              Citizen Report
            </div>
         </GlassPanel>
      </div>
    </div>
  );
}
