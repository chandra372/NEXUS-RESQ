import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { Layers, Navigation, ExternalLink } from 'lucide-react';
import { IncidentSummary } from '../types';

interface LiveMapProps {
  incidents: IncidentSummary[];
  selectedIncident: IncidentSummary | null;
  onSelectIncident: (inc: IncidentSummary) => void;
}

const GOOGLE_MAPS_KEY =
  import.meta.env.VITE_GOOGLE_MAPS_API_KEY || 'AIzaSyBOjAJwIB_Djq0aILqxl_oMLGrcELKOFwA';

type MapLayerType = 'tactical' | 'google-hybrid' | 'google-roadmap' | 'google-terrain';

const TILE_LAYERS: Record<
  MapLayerType,
  { label: string; icon: string; url: string; attribution: string; subdomains?: string[] }
> = {
  tactical: {
    label: 'Tactical Dark',
    icon: '🌙',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; CARTO',
    subdomains: ['a', 'b', 'c', 'd'],
  },
  'google-hybrid': {
    label: 'Google Satellite',
    icon: '🛰️',
    url: `https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_KEY}`,
    attribution: '&copy; Google Maps',
  },
  'google-roadmap': {
    label: 'Google Streets',
    icon: '🗺️',
    url: `https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_KEY}`,
    attribution: '&copy; Google Maps',
  },
  'google-terrain': {
    label: 'Google Terrain',
    icon: '⛰️',
    url: `https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}&key=${GOOGLE_MAPS_KEY}`,
    attribution: '&copy; Google Maps',
  },
};

export const LiveMap: React.FC<LiveMapProps> = ({
  incidents,
  selectedIncident,
  onSelectIncident,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const currentTileLayerRef = useRef<L.TileLayer | null>(null);
  const markersRef = useRef<{ [key: string]: L.Marker | L.Circle }>({});
  const [activeLayer, setActiveLayer] = useState<MapLayerType>('tactical');

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center on Chennai emergency area (Velachery / Tambaram / Medavakkam)
    const map = L.map(mapContainerRef.current, {
      center: [12.955, 80.185],
      zoom: 12,
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    const initialConfig = TILE_LAYERS['tactical'];
    const tileLayer = L.tileLayer(initialConfig.url, {
      attribution: initialConfig.attribution,
      maxZoom: 20,
      subdomains: initialConfig.subdomains || ['a'],
    }).addTo(map);

    currentTileLayerRef.current = tileLayer;
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Handle Layer Switch
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (currentTileLayerRef.current) {
      map.removeLayer(currentTileLayerRef.current);
    }

    const config = TILE_LAYERS[activeLayer];
    const newTileLayer = L.tileLayer(config.url, {
      attribution: config.attribution,
      maxZoom: 20,
      subdomains: config.subdomains || ['a'],
    }).addTo(map);

    newTileLayer.bringToBack();
    currentTileLayerRef.current = newTileLayer;
  }, [activeLayer]);

  // Update incident markers
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear old markers
    Object.values(markersRef.current).forEach((m) => m.remove());
    markersRef.current = {};

    incidents.forEach((inc) => {
      if (inc.latitude && inc.longitude) {
        const isCritical = inc.priority_level === 'CRITICAL';
        const isResolved = inc.is_resolved;
        const isSelected = selectedIncident?.incident_id === inc.incident_id;

        const color = isResolved
          ? '#10b981' // emerald
          : isCritical
          ? '#ef4444' // red
          : inc.priority_level === 'HIGH'
          ? '#f97316' // orange
          : '#eab308'; // yellow

        // Custom HTML marker
        const iconHtml = `
          <div class="relative flex items-center justify-center">
            ${isCritical ? '<div class="absolute w-10 h-10 rounded-full bg-red-500/30 pulsing-ring pointer-events-none"></div>' : ''}
            <div class="w-7 h-7 rounded-full flex items-center justify-center font-bold text-[10px] text-white shadow-lg border-2 ${
              isSelected ? 'border-cyan-300 scale-125' : 'border-slate-900'
            }" style="background-color: ${color};">
              ${inc.current_people ?? '!'}
            </div>
          </div>
        `;

        const customIcon = L.divIcon({
          html: iconHtml,
          className: 'custom-emergency-pin',
          iconSize: [28, 28],
          iconAnchor: [14, 14],
        });

        const googleMapsNavUrl = `https://www.google.com/maps/dir/?api=1&destination=${inc.latitude},${inc.longitude}`;

        const marker = L.marker([inc.latitude, inc.longitude], { icon: customIcon })
          .addTo(map)
          .bindPopup(`
            <div class="p-2 min-w-50 text-slate-100 font-sans">
              <div class="flex items-center justify-between gap-2 mb-1">
                <span class="font-bold text-xs text-indigo-400 font-mono">${inc.incident_id}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded font-bold" style="background-color: ${color}20; color: ${color};">
                  ${inc.status}
                </span>
              </div>
              <h4 class="font-bold text-xs text-white line-clamp-2 mb-1">${inc.name}</h4>
              <p class="text-[11px] text-slate-400 mb-2">${inc.canonical_location}</p>
              <div class="text-[11px] flex justify-between text-slate-300 mb-2">
                <span>People: <strong>${inc.current_people ?? 'Unknown'}</strong></span>
                <span>Priority: <strong>${inc.priority_score}</strong></span>
              </div>
              <button 
                id="btn-view-${inc.incident_id}"
                style="width: 100%; background: #4f46e5; color: white; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; border: none; cursor: pointer; margin-bottom: 4px;"
              >
                Inspect Incident Evidence
              </button>
              <a 
                href="${googleMapsNavUrl}"
                target="_blank"
                rel="noopener noreferrer"
                style="display: flex; align-items: center; justify-content: center; gap: 4px; width: 100%; background: rgba(30, 41, 59, 0.9); color: #38bdf8; padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: 600; border: 1px solid rgba(56, 189, 248, 0.2); text-decoration: none;"
              >
                📍 Open in Google Maps
              </a>
            </div>
          `);

        marker.on('popupopen', () => {
          const btn = document.getElementById(`btn-view-${inc.incident_id}`);
          if (btn) {
            btn.onclick = () => onSelectIncident(inc);
          }
        });

        markersRef.current[inc.incident_id] = marker;

        // Approximate radius circle where location precision is area
        if (inc.location_precision === 'area') {
          const circle = L.circle([inc.latitude, inc.longitude], {
            radius: 800,
            color: color,
            fillColor: color,
            fillOpacity: 0.08,
            weight: 1,
            dashArray: '4, 4',
          }).addTo(map);
          markersRef.current[`${inc.incident_id}_circle`] = circle;
        }
      }
    });
  }, [incidents, selectedIncident, onSelectIncident]);

  return (
    <div className="relative w-full h-full min-h-105 rounded-xl overflow-hidden border border-slate-800 shadow-md">
      <div ref={mapContainerRef} className="w-full h-full min-h-105 bg-slate-950 z-10" />

      {/* Top Left Status Badge */}
      <div className="absolute top-3 left-3 z-20 bg-slate-900/90 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-slate-800 text-[11px] text-slate-300 shadow flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span className="font-bold text-white">Geographic Dispatcher Map</span>
        <span className="text-slate-500">•</span>
        <span className="text-slate-400">Chennai Operations</span>
      </div>

      {/* Top Right Google Maps Layer Switcher */}
      <div className="absolute top-3 right-3 z-20 bg-slate-900/90 backdrop-blur-md p-1 rounded-lg border border-slate-800 shadow flex items-center gap-1">
        {(Object.keys(TILE_LAYERS) as MapLayerType[]).map((key) => {
          const layer = TILE_LAYERS[key];
          const isSelected = activeLayer === key;
          return (
            <button
              key={key}
              onClick={() => setActiveLayer(key)}
              title={layer.label}
              className={`px-2 py-1 rounded text-xs font-medium transition cursor-pointer flex items-center gap-1.5 ${
                isSelected
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <span>{layer.icon}</span>
              <span className="hidden sm:inline">{layer.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
