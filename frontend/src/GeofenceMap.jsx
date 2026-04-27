import React, { useEffect } from 'react';
import { MapContainer, TileLayer, CircleMarker, Circle, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    map.setView([center.lat, center.lon], map.getZoom());
  }, [center.lat, center.lon, map]);
  return null;
}

export default function GeofenceMap({ pois, geofenceRadiusM, mapCenter }) {
  if (!mapCenter || pois.length === 0) return null;

  const center = [mapCenter.lat, mapCenter.lon];

  return (
    <div className="mt-4 overflow-hidden rounded-xl border border-slate-200" style={{ height: '320px' }}>
      <MapContainer
        center={center}
        zoom={14}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <RecenterMap center={mapCenter} />

        {/* Geofence circle */}
        {geofenceRadiusM && (
          <Circle
            center={center}
            radius={geofenceRadiusM}
            pathOptions={{ color: '#6366f1', fillColor: '#6366f1', fillOpacity: 0.08, weight: 2 }}
          />
        )}

        {/* POI pins */}
        {pois.map((poi, i) => (
          <CircleMarker
            key={i}
            center={[poi.lat, poi.lon]}
            radius={6}
            pathOptions={{ color: '#0f172a', fillColor: '#f59e0b', fillOpacity: 1, weight: 2 }}
          >
            <Popup>
              <strong>{poi.name}</strong><br />
              {poi.type} · {Math.round(poi.distance_m)}m away
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
