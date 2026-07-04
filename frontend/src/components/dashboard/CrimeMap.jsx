import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { GlassPanel } from '../ui';
import './CrimeMap.css';

const SEVERITY_COLORS = {
  CRITICAL: 'var(--accent-risk)',
  HIGH: 'var(--accent-risk)',
  MEDIUM: 'var(--accent-warning)',
  LOW: 'var(--accent-trust)',
  SAFE: 'var(--accent-trust)',
};

// Component to dynamically re-center map if selected event changes
function MapController({ selectedEvent }) {
  const map = useMap();
  useEffect(() => {
    if (selectedEvent?.location) {
      map.flyTo([selectedEvent.location.lat, selectedEvent.location.lng], 14, {
        duration: 1.5,
      });
    }
  }, [selectedEvent, map]);
  return null;
}

export function CrimeMap({ hotspots = [], loading, selectedEvent }) {
  // NYC default center
  const center = [40.7128, -74.0060];

  return (
    <div className="crime-map-container">
      <MapContainer 
        center={center} 
        zoom={12} 
        style={{ height: '100%', width: '100%', background: 'var(--bg-base)' }}
        zoomControl={false}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
        />
        
        <MapController selectedEvent={selectedEvent} />

        {!loading && hotspots.map((spot) => (
          <CircleMarker
            key={spot.id}
            center={[spot.lat, spot.lng]}
            pathOptions={{
              color: SEVERITY_COLORS[spot.type],
              fillColor: SEVERITY_COLORS[spot.type],
              fillOpacity: 0.2 + (spot.intensity * 0.4),
              weight: 1,
            }}
            radius={Math.max(10, spot.intensity * 30)}
            className={spot.type === 'CRITICAL' ? 'breathing-marker' : ''}
          >
            <Popup className="dark-popup">
              <strong>{spot.type} Cluster</strong><br/>
              Intensity: {(spot.intensity * 100).toFixed(0)}%
            </Popup>
          </CircleMarker>
        ))}

        {selectedEvent && (
          <CircleMarker
            center={[selectedEvent.location.lat, selectedEvent.location.lng]}
            pathOptions={{
              color: '#fff',
              fillColor: 'var(--accent-risk)',
              fillOpacity: 1,
              weight: 2,
            }}
            radius={8}
            className="pulse-marker"
          >
             <Popup className="dark-popup">{selectedEvent.title}</Popup>
          </CircleMarker>
        )}
      </MapContainer>
      
      {/* Overlay Status */}
      <div className="crime-map-overlay">
         <GlassPanel hoverable={false} className="map-legend">
            <span className="legend-title">Live Grid Status</span>
            <div className="legend-item"><span className="legend-dot critical"></span> Critical Hotspots</div>
            <div className="legend-item"><span className="legend-dot warning"></span> Elevated Activity</div>
         </GlassPanel>
      </div>
    </div>
  );
}
