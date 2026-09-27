'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  MapPointItem,
  OfficialIndiaMapProvider,
  GisMapMode,
  GisLayerVisibility,
  GisProviderStatus
} from '../types';
import {
  Radar,
  Navigation,
  Info,
  Layers,
  Crosshair,
  Loader2,
  AlertTriangle,
  Route,
  X,
  MapPin,
  ShieldCheck,
  Compass,
  CheckSquare,
  Square,
  Globe2,
  SlidersHorizontal,
  ChevronDown,
  Building2,
  Truck
} from 'lucide-react';
import {
  getOfficialMapProvider,
  getRenderedMapStatus,
  getGisProviderStatus,
  getLayerConfigurationForMode,
  DEFAULT_GIS_MODE,
  DEFAULT_LAYER_VISIBILITY,
  INDIA_MAP_BOUNDS,
  MAP_FALLBACK_LABEL,
  MAP_FALLBACK_TILE_URL,
  MAP_FALLBACK_ATTRIBUTION,
  OFFICIAL_MAP_ATTRIBUTION,
  OFFICIAL_MAP_TILE_URL
} from '../lib/map-config';
import {
  INDIA_ADMIN_GEOJSON,
  INDIA_KEY_SOURCING_DISTRICTS,
  INDIA_LOGISTICS_CORRIDORS
} from '../lib/india-admin-gis';

interface SourcingMapProps {
  points: MapPointItem[];
  selectedPointId?: string | null;
  onSelectPoint?: (id: string) => void;
}

export const SourcingMap: React.FC<SourcingMapProps> = ({
  points,
  selectedPointId,
  onSelectPoint
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<Record<string, any>>({});
  const regionCirclesRef = useRef<Record<string, any>>({});
  const [isMapReady, setIsMapReady] = useState(false);

  // Map Provider State (Official Government of India Provider abstraction)
  const [mapProvider, setMapProvider] = useState<OfficialIndiaMapProvider>(() => getOfficialMapProvider());

  // GIS Mode & Layer Visibility State
  const [mapMode, setMapMode] = useState<GisMapMode>(DEFAULT_GIS_MODE);
  const [layersVisibility, setLayersVisibility] = useState<GisLayerVisibility>(DEFAULT_LAYER_VISIBILITY);
  const [isLayersPanelOpen, setIsLayersPanelOpen] = useState<boolean>(false);

  // Leaflet LayerGroups references for dynamic toggling without destroying markers
  const baseTileLayerRef = useRef<any>(null);
  const adminBoundariesGroupRef = useRef<any>(null);
  const districtBoundariesGroupRef = useRef<any>(null);
  const roadLogisticsGroupRef = useRef<any>(null);
  const sourcingRegionsGroupRef = useRef<any>(null);
  const procurementSourcesGroupRef = useRef<any>(null);
  const buyerLocationGroupRef = useRef<any>(null);
  const routeGroupRef = useRef<any>(null);

  // Live User Location State (on-demand only, never continuously tracked)
  const [userLocation, setUserLocation] = useState<{
    lat: number;
    lng: number;
    accuracy: number;
  } | null>(null);
  const [isLocating, setIsLocating] = useState<boolean>(false);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const userMarkerRef = useRef<any>(null);
  const userAccuracyCircleRef = useRef<any>(null);

  // Directions & Routing State
  const [isRouting, setIsRouting] = useState<boolean>(false);
  const [routingError, setRoutingError] = useState<string | null>(null);
  const [activeRoute, setActiveRoute] = useState<{
    destinationId: string;
    destinationTitle: string;
    destinationType: string;
    isRegion: boolean;
    distanceKm: number;
    durationMinutes: number;
  } | null>(null);
  const routePolylineRef = useRef<any>(null);

  // Find currently selected point
  const selectedPoint = points.find((p) => p.id === selectedPointId) || null;

  // Compute structured provider attribution for honest GIS HUD
  const providerStatus: GisProviderStatus = getGisProviderStatus(
    mapProvider,
    mapMode,
    layersVisibility,
    !!activeRoute
  );

  // 1. Initialize Map with GIS Panes and Layer Groups
  useEffect(() => {
    if (typeof window === 'undefined' || !mapContainerRef.current) return;

    let isMounted = true;

    import('leaflet').then((L) => {
      if (!isMounted || !mapContainerRef.current) return;

      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }

      // India geographic bounds: 6.0°N to 37.5°N, 68.0°E to 97.5°E
      const indiaBounds = L.latLngBounds(
        [INDIA_MAP_BOUNDS.south, INDIA_MAP_BOUNDS.west],
        [INDIA_MAP_BOUNDS.north, INDIA_MAP_BOUNDS.east]
      );

      const map = L.map(mapContainerRef.current, {
        maxBounds: indiaBounds,
        maxBoundsViscosity: 1.0,
        minZoom: 4,
        maxZoom: 13,
        zoomSnap: 0.5,
        zoomControl: true,
        attributionControl: true
      });

      // Create GIS Panes for strict visual hierarchy
      const districtPane = map.createPane('districtBoundariesPane');
      districtPane.style.zIndex = '320';

      const adminPane = map.createPane('adminBoundariesPane');
      adminPane.style.zIndex = '340';

      const roadPane = map.createPane('roadLogisticsPane');
      roadPane.style.zIndex = '370';

      const routePane = map.createPane('routeDirectionsPane');
      routePane.style.zIndex = '430';

      const regionPane = map.createPane('sourcingRegionsPane');
      regionPane.style.zIndex = '460';

      const sourcePane = map.createPane('procurementSourcesPane');
      sourcePane.style.zIndex = '520';

      const gpsPane = map.createPane('buyerGpsPane');
      gpsPane.style.zIndex = '600';

      // Initialize empty LayerGroups
      adminBoundariesGroupRef.current = L.layerGroup([], { pane: 'adminBoundariesPane' }).addTo(map);
      districtBoundariesGroupRef.current = L.layerGroup([], { pane: 'districtBoundariesPane' }).addTo(map);
      roadLogisticsGroupRef.current = L.layerGroup([], { pane: 'roadLogisticsPane' }).addTo(map);
      sourcingRegionsGroupRef.current = L.layerGroup([], { pane: 'sourcingRegionsPane' }).addTo(map);
      procurementSourcesGroupRef.current = L.layerGroup([], { pane: 'procurementSourcesPane' }).addTo(map);
      buyerLocationGroupRef.current = L.layerGroup([], { pane: 'buyerGpsPane' }).addTo(map);
      routeGroupRef.current = L.layerGroup([], { pane: 'routeDirectionsPane' }).addTo(map);

      // Initialize Administrative Reference Boundaries (Subtle context)
      const adminLayer = L.geoJSON(INDIA_ADMIN_GEOJSON, {
        pane: 'adminBoundariesPane',
        style: (feature: any) => {
          if (feature?.properties?.category === 'NATIONAL_BOUNDARY') {
            return {
              color: '#64748b',
              weight: 1.2,
              opacity: 0.35,
              fillColor: '#94a3b8',
              fillOpacity: 0
            };
          }
          return {
            color: '#94a3b8',
            weight: 0.7,
            opacity: 0.20,
            dashArray: '2, 4',
            fillColor: '#94a3b8',
            fillOpacity: 0
          };
        },
        onEachFeature: (feature: any, layer: any) => {
          if (feature.properties) {
            const name = feature.properties.name;
            layer.bindTooltip(
              `<div class="font-mono text-[9px] text-slate-200 font-medium px-1 py-0.5">${name}</div>`,
              { sticky: true, opacity: 0.85, className: 'compact-gis-tooltip', direction: 'auto' }
            );
          }
        }
      });
      adminBoundariesGroupRef.current.addLayer(adminLayer);

      // Initialize District Boundaries Layer (Very subtle reference dots)
      INDIA_KEY_SOURCING_DISTRICTS.forEach((d) => {
        const districtMarker = L.circleMarker([d.coordinates[0], d.coordinates[1]], {
          pane: 'districtBoundariesPane',
          radius: 2,
          color: '#64748b',
          fillColor: '#94a3b8',
          fillOpacity: 0.25,
          weight: 0.8
        }).bindTooltip(
          `<div class="font-mono text-[9px] font-medium text-slate-200 px-1 py-0.5"><span class="text-slate-400">District:</span> ${d.district} (${d.state})</div>`,
          { direction: 'bottom', opacity: 0.85, className: 'compact-gis-tooltip', offset: [0, 4] }
        );
        districtBoundariesGroupRef.current.addLayer(districtMarker);
      });

      // Initialize Operational Road / Logistics Corridors Layer (Moderate freight spine)
      INDIA_LOGISTICS_CORRIDORS.forEach((c) => {
        const roadLine = L.polyline(c.coordinates, {
          pane: 'roadLogisticsPane',
          color: '#0284c7',
          weight: 1.5,
          opacity: 0.38,
          dashArray: '4, 6'
        }).bindTooltip(
          `<div class="font-mono text-[10px] font-bold text-sky-200 px-1 py-0.5"><span class="text-sky-400 font-extrabold">${c.highwayCode}</span> &bull; ${c.name}</div>`,
          { sticky: true, opacity: 0.9, className: 'compact-gis-tooltip' }
        );

        roadLine.on('mouseover', () => {
          roadLine.setStyle({ weight: 2.2, opacity: 0.70 });
        });
        roadLine.on('mouseout', () => {
          roadLine.setStyle({ weight: 1.5, opacity: 0.38 });
        });

        roadLogisticsGroupRef.current.addLayer(roadLine);
      });

      // Configure Base Map Provider
      const provider = getOfficialMapProvider();
      setMapProvider(provider);

      let activeTileLayer: any = null;

      if (provider.serviceType === 'WMS' && provider.endpointUrl) {
        // Official Government of India WMS Layer (NIC Bharat Maps, Survey of India, or ISRO Bhuvan)
        activeTileLayer = L.tileLayer.wms(provider.endpointUrl, {
          layers: provider.layerName,
          format: 'image/png',
          transparent: true,
          version: '1.1.1',
          attribution: provider.attribution,
          minZoom: provider.minZoom,
          maxZoom: provider.maxZoom
        }).addTo(map);

        activeTileLayer.on('tileerror', () => {
          setMapProvider((prev) => ({
            ...prev,
            error: `Unable to load tiles from ${provider.name} (${provider.endpointUrl})`
          }));
        });
      } else if (provider.endpointUrl) {
        // Tile layer (e.g. Development Fallback with explicit attribution)
        // Fallback URL: https://tile.openstreetmap.org/{z}/{x}/{y}.png
        // Development fallback — OpenStreetMap
        activeTileLayer = L.tileLayer(provider.endpointUrl, {
          attribution: provider.attribution,
          minZoom: provider.minZoom,
          maxZoom: provider.maxZoom
        }).addTo(map);

        activeTileLayer.on('tileerror', () => {
          setMapProvider((prev) => ({
            ...prev,
            error: `Unable to load basemap tiles from ${provider.name}`
          }));
        });
      }

      baseTileLayerRef.current = activeTileLayer;

      map.fitBounds(indiaBounds, { padding: [10, 10] });

      mapInstanceRef.current = map;
      setIsMapReady(true);
    });

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Render Procurement Sourcing Points (Regions & Sources LayerGroups)
  useEffect(() => {
    if (!isMapReady || !mapInstanceRef.current || typeof window === 'undefined') return;

    import('leaflet').then((L) => {
      const map = mapInstanceRef.current;
      if (!map) return;

      // Clear existing markers and corridor circles
      if (sourcingRegionsGroupRef.current) sourcingRegionsGroupRef.current.clearLayers();
      if (procurementSourcesGroupRef.current) procurementSourcesGroupRef.current.clearLayers();
      markersRef.current = {};
      regionCirclesRef.current = {};

      const indiaBounds = L.latLngBounds([6.0, 68.0], [37.5, 97.5]);

      if (!points || points.length === 0) {
        map.fitBounds(indiaBounds, { padding: [10, 10] });
        return;
      }

      const bounds = L.latLngBounds([]);

      points.forEach((point) => {
        const isSelected = point.id === selectedPointId;
        const vStat = (point.verification_status || '').toUpperCase();
        const pLabel = (point.provenance_label || '').toUpperCase();
        const sType = (point.source_type || '').toUpperCase();

        const isBuyerVerified = pLabel === 'BUYER_VERIFIED' || vStat === 'CONFIRMED';
        const isRegion = sType === 'SOURCING_REGION' || vStat === 'REGION_ONLY' || pLabel === 'REGION_ONLY';
        const isUnverified = sType === 'SUPPLIER' || sType === 'DISTRIBUTOR' || vStat === 'UNVERIFIED' || vStat === 'REQUIRES_VENDOR_VERIFICATION';

        let markerColor = '#f59e0b';
        let badgeColor = '#fbbf24';
        let badgeBg = 'rgba(245, 158, 11, 0.2)';
        let statusLabel = 'Requires Live Verification';

        if (isBuyerVerified) {
          markerColor = '#10b981';
          badgeColor = '#34d399';
          badgeBg = 'rgba(16, 185, 129, 0.2)';
          statusLabel = 'Buyer Verified (Live)';
        } else if (isRegion) {
          markerColor = '#3b82f6';
          badgeColor = '#60a5fa';
          badgeBg = 'rgba(59, 130, 246, 0.2)';
          statusLabel = 'Region Only';
        } else if (isUnverified) {
          markerColor = '#f43f5e';
          badgeColor = '#fb7185';
          badgeBg = 'rgba(244, 63, 94, 0.2)';
          statusLabel = 'Unverified';
        }

        // Calculate visual hierarchy priority zIndexOffset
        // Priority: BUYER GPS (3000) > verified source (2500) > requires-live-verification source (2000) > unverified source (1500) > REGION_ONLY (1000) > logistics corridor > administrative boundary
        let zIndexOffset = 1000;
        if (isBuyerVerified) {
          zIndexOffset = 2500;
        } else if (vStat === 'REQUIRES_LIVE_VERIFICATION' || sType === 'MANUFACTURER') {
          zIndexOffset = 2000;
        } else if (isUnverified) {
          zIndexOffset = 1500;
        } else if (isRegion) {
          zIndexOffset = 1000;
        }
        if (isSelected) {
          zIndexOffset += 500;
        }

        // If it is a sourcing region, render a distinct 25km corridor radius circle (strong but translucent)
        if (isRegion) {
          const corridorCircle = L.circle([point.latitude, point.longitude], {
            pane: 'sourcingRegionsPane',
            radius: 25000, // 25 km representative corridor area
            color: '#2563eb',
            weight: 1.3,
            dashArray: '4, 6',
            fillColor: '#3b82f6',
            fillOpacity: 0.08
          });
          sourcingRegionsGroupRef.current.addLayer(corridorCircle);
          regionCirclesRef.current[point.id] = corridorCircle;
        }

        const markerHtml = `
          <div style="position: relative; display: flex; align-items: center; justify-content: center;">
            <div style="
              width: ${isSelected ? '24px' : '16px'};
              height: ${isSelected ? '24px' : '16px'};
              background: ${markerColor};
              border: 2px solid #ffffff;
              border-radius: ${isRegion ? '50%' : '4px'};
              box-shadow: 0 0 ${isSelected ? '14px' : '8px'} ${markerColor}, 0 2px 4px rgba(0,0,0,0.5);
              display: flex;
              align-items: center;
              justify-content: center;
              cursor: pointer;
              transition: all 0.2s ease;
            ">
              <div style="width: 4px; height: 4px; background: white; border-radius: 50%;"></div>
            </div>
            ${isSelected ? `<div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; border: 2px solid ${markerColor}; opacity: 0.7; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>` : ''}
          </div>
        `;

        const customIcon = L.divIcon({
          className: 'custom-leaflet-marker',
          html: markerHtml,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
          popupAnchor: [0, -16]
        });

        const marker = L.marker([point.latitude, point.longitude], {
          icon: customIcon,
          pane: isRegion ? 'sourcingRegionsPane' : 'procurementSourcesPane',
          zIndexOffset
        });

        // Compact hover tooltip (non-intrusive, pointer-events: none)
        marker.bindTooltip(
          `<div class="font-mono text-[10px] font-bold text-slate-100">${point.title}</div>
           <div class="font-mono text-[9px] text-slate-300">${point.location} &bull; ${Math.round(point.suitability_score * 100)}% Match</div>`,
          {
            direction: 'top',
            offset: [0, -14],
            opacity: 0.95,
            className: 'compact-source-tooltip'
          }
        );

        const standardsText = point.relevant_standards && point.relevant_standards.length > 0
          ? point.relevant_standards.slice(0, 3).join(', ')
          : 'Standards Conforming';

        const evidenceHtml = point.evidence_preview && point.evidence_preview.length > 0
          ? `<div style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed #334155; font-size: 9px; color: #94a3b8;">
               <strong style="color: #cbd5e1;">Evidence:</strong> ${point.evidence_preview[0]}
             </div>`
          : '';

        const popupContent = `
          <div style="font-family: system-ui, sans-serif; font-size: 11px; color: #f8fafc; padding: 4px; min-width: 210px; max-width: 260px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-size: 9px; font-weight: 700; color: ${badgeColor}; background: ${badgeBg}; padding: 2px 5px; border-radius: 3px; text-transform: uppercase; font-family: monospace;">
                ${statusLabel}
              </span>
              <span style="font-weight: 700; color: #38bdf8; font-size: 11px; font-family: monospace;">
                ${Math.round(point.suitability_score * 100)}% Match
              </span>
            </div>
            <div style="font-weight: 700; font-size: 12px; color: #ffffff; margin-bottom: 2px;">
              ${point.title}
            </div>
            <div style="font-size: 10px; color: #94a3b8; margin-bottom: 4px;">
              📍 ${point.location}
            </div>
            <div style="font-size: 10px; margin-bottom: 2px; color: #cbd5e1;">
              <strong style="color: #e2e8f0;">Range:</strong> ${point.distance_from_buyer_km != null ? `${point.distance_from_buyer_km} km / ${point.range_status || 'DISTANCE'}` : 'Distance unknown'}
            </div>
            <div style="font-size: 10px; margin-bottom: 2px; color: #cbd5e1;">
              <strong style="color: #e2e8f0;">Record:</strong> ${point.official_record_status || 'UNVERIFIED'}
            </div>
            <div style="font-size: 10px; margin-bottom: 2px; color: #cbd5e1;">
              <strong style="color: #e2e8f0;">Items:</strong> ${point.supported_items.slice(0, 2).join(', ')}
            </div>
            <div style="font-size: 10px; margin-bottom: 2px; color: #cbd5e1;">
              <strong style="color: #e2e8f0;">Standards:</strong> <span style="font-family: monospace; color: #fbbf24;">${standardsText}</span>
            </div>
            ${evidenceHtml}
            <div style="margin-top: 5px; padding-top: 5px; border-top: 1px solid #334155; font-size: 9px; color: #94a3b8; text-align: center;">
              Select below for directions & route details
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);

        marker.on('click', () => {
          if (onSelectPoint) onSelectPoint(point.id);
        });

        markersRef.current[point.id] = marker;
        bounds.extend([point.latitude, point.longitude]);

        // Place into appropriate layer group
        if (isRegion) {
          sourcingRegionsGroupRef.current.addLayer(marker);
        } else {
          procurementSourcesGroupRef.current.addLayer(marker);
        }
      });

      if (points.length > 1) {
        map.fitBounds(bounds, { padding: [40, 40], maxZoom: 8 });
      } else if (points.length === 1) {
        map.setView([points[0].latitude, points[0].longitude], 6);
      }

      if (selectedPointId && markersRef.current[selectedPointId]) {
        const selectedPt = points.find((p) => p.id === selectedPointId);
        if (selectedPt) {
          map.panTo([selectedPt.latitude, selectedPt.longitude]);
          markersRef.current[selectedPointId].openPopup();
        }
      }
    });
  }, [points, isMapReady, selectedPointId, onSelectPoint]);

  // 3. Dynamic GIS Mode & Layer Toggles (Without Destroying Map or Markers)
  useEffect(() => {
    if (!isMapReady || !mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    // Toggle Administrative Boundaries
    if (adminBoundariesGroupRef.current) {
      if (layersVisibility.administrativeBoundaries && !map.hasLayer(adminBoundariesGroupRef.current)) {
        map.addLayer(adminBoundariesGroupRef.current);
      } else if (!layersVisibility.administrativeBoundaries && map.hasLayer(adminBoundariesGroupRef.current)) {
        map.removeLayer(adminBoundariesGroupRef.current);
      }
    }

    // Toggle District Boundaries
    if (districtBoundariesGroupRef.current) {
      if (layersVisibility.districtBoundaries && !map.hasLayer(districtBoundariesGroupRef.current)) {
        map.addLayer(districtBoundariesGroupRef.current);
      } else if (!layersVisibility.districtBoundaries && map.hasLayer(districtBoundariesGroupRef.current)) {
        map.removeLayer(districtBoundariesGroupRef.current);
      }
    }

    // Toggle Road / Logistics Network
    if (roadLogisticsGroupRef.current) {
      if (layersVisibility.roadLogistics && !map.hasLayer(roadLogisticsGroupRef.current)) {
        map.addLayer(roadLogisticsGroupRef.current);
      } else if (!layersVisibility.roadLogistics && map.hasLayer(roadLogisticsGroupRef.current)) {
        map.removeLayer(roadLogisticsGroupRef.current);
      }
    }

    // Toggle Sourcing Regions
    if (sourcingRegionsGroupRef.current) {
      if (layersVisibility.sourcingRegions && !map.hasLayer(sourcingRegionsGroupRef.current)) {
        map.addLayer(sourcingRegionsGroupRef.current);
      } else if (!layersVisibility.sourcingRegions && map.hasLayer(sourcingRegionsGroupRef.current)) {
        map.removeLayer(sourcingRegionsGroupRef.current);
      }
    }

    // Toggle Procurement Sources
    if (procurementSourcesGroupRef.current) {
      if (layersVisibility.procurementSources && !map.hasLayer(procurementSourcesGroupRef.current)) {
        map.addLayer(procurementSourcesGroupRef.current);
      } else if (!layersVisibility.procurementSources && map.hasLayer(procurementSourcesGroupRef.current)) {
        map.removeLayer(procurementSourcesGroupRef.current);
      }
    }

    // Toggle Live GPS
    if (buyerLocationGroupRef.current) {
      if (layersVisibility.liveGps && !map.hasLayer(buyerLocationGroupRef.current)) {
        map.addLayer(buyerLocationGroupRef.current);
      } else if (!layersVisibility.liveGps && map.hasLayer(buyerLocationGroupRef.current)) {
        map.removeLayer(buyerLocationGroupRef.current);
      }
    }

    // Toggle Routes
    if (routeGroupRef.current) {
      if (layersVisibility.routes && !map.hasLayer(routeGroupRef.current)) {
        map.addLayer(routeGroupRef.current);
      } else if (!layersVisibility.routes && map.hasLayer(routeGroupRef.current)) {
        map.removeLayer(routeGroupRef.current);
      }
    }
  }, [layersVisibility, isMapReady]);

  // Mode Switch Handler
  const handleModeChange = (newMode: GisMapMode) => {
    setMapMode(newMode);
    const updatedLayers = getLayerConfigurationForMode(newMode, layersVisibility);
    setLayersVisibility(updatedLayers);
  };

  // Toggle Individual Layer
  const handleToggleLayer = (key: keyof GisLayerVisibility) => {
    setLayersVisibility((prev) => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // 4. Handle Live Geolocation (On-Demand only)
  const handleUseMyLocation = () => {
    if (typeof window === 'undefined' || !navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser.');
      return;
    }

    setIsLocating(true);
    setLocationError(null);
    setLocationStatus(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords;
        setUserLocation({ lat: latitude, lng: longitude, accuracy });
        setIsLocating(false);

        const accuracyText = accuracy < 100
          ? `High accuracy (~${Math.round(accuracy)}m)`
          : `Approximate (~${Math.round(accuracy)}m)`;
        setLocationStatus(`GPS acquired: ${accuracyText}`);

        // Automatically enable liveGps layer visibility
        setLayersVisibility((prev) => ({ ...prev, liveGps: true }));

        import('leaflet').then((L) => {
          const map = mapInstanceRef.current;
          if (!map || !buyerLocationGroupRef.current) return;

          buyerLocationGroupRef.current.clearLayers();

          // User accuracy circle
          userAccuracyCircleRef.current = L.circle([latitude, longitude], {
            pane: 'buyerGpsPane',
            radius: accuracy,
            color: '#0284c7',
            fillColor: '#38bdf8',
            fillOpacity: 0.15,
            weight: 1.5
          });
          buyerLocationGroupRef.current.addLayer(userAccuracyCircleRef.current);

          // Distinct user marker (Cyan pulsating circle)
          const userIconHtml = `
            <div style="position: relative; display: flex; align-items: center; justify-content: center;">
              <div style="
                width: 18px;
                height: 18px;
                background: #0284c7;
                border: 2.5px solid #ffffff;
                border-radius: 50%;
                box-shadow: 0 0 12px #38bdf8;
                display: flex;
                align-items: center;
                justify-content: center;
              ">
                <div style="width: 5px; height: 5px; background: white; border-radius: 50%;"></div>
              </div>
              <div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; border: 2px solid #38bdf8; opacity: 0.6; animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
            </div>
          `;

          const userIcon = L.divIcon({
            className: 'user-location-marker',
            html: userIconHtml,
            iconSize: [34, 34],
            iconAnchor: [17, 17]
          });

          userMarkerRef.current = L.marker([latitude, longitude], {
            icon: userIcon,
            pane: 'buyerGpsPane',
            zIndexOffset: 3000
          }).bindPopup(`
            <div style="font-family: system-ui, sans-serif; font-size: 11px; color: #f8fafc; padding: 4px;">
              <div style="font-weight: 700; color: #38bdf8; margin-bottom: 2px;">📍 Your Current Location</div>
              <div style="font-size: 10px; color: #94a3b8;">Accuracy: &plusmn;${Math.round(accuracy)} meters</div>
              <div style="font-size: 10px; color: #cbd5e1; margin-top: 3px;">Starting point for sourcing navigation</div>
            </div>
          `);
          buyerLocationGroupRef.current.addLayer(userMarkerRef.current);

          map.setView([latitude, longitude], Math.min(map.getZoom() || 6, 8));
        });
      },
      (error) => {
        setIsLocating(false);
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Location permission denied by user. Please enable location access in browser settings.');
            break;
          case error.POSITION_UNAVAILABLE:
            setLocationError('Location information is currently unavailable from your device.');
            break;
          case error.TIMEOUT:
            setLocationError('Location request timed out. Please try again.');
            break;
          default:
            setLocationError('Unable to acquire device location.');
            break;
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000
      }
    );
  };

  // 5. Calculate Driving Directions via OSRM (Operational Logistics)
  const handleGetDirections = async (point: MapPointItem) => {
    setRoutingError(null);

    if (!userLocation) {
      setRoutingError('Please click "Use My Location" first to establish your starting location for directions.');
      return;
    }

    setIsRouting(true);

    const sType = (point.source_type || '').toUpperCase();
    const vStat = (point.verification_status || '').toUpperCase();
    const isRegion = sType === 'SOURCING_REGION' || vStat === 'REGION_ONLY';

    const routingBaseUrl = process.env.NEXT_PUBLIC_ROUTING_API_URL || 'https://router.project-osrm.org/route/v1/driving';

    try {
      const url = `${routingBaseUrl}/${userLocation.lng},${userLocation.lat};${point.longitude},${point.latitude}?overview=full&geometries=geojson`;
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(`Routing service returned status ${res.status}`);
      }

      const data = await res.json();
      if (!data.routes || data.routes.length === 0) {
        throw new Error('No valid driving route found between coordinates.');
      }

      const primaryRoute = data.routes[0];
      const distanceMeters = primaryRoute.distance;
      const durationSeconds = primaryRoute.duration;
      const geojsonCoords = primaryRoute.geometry.coordinates;

      // Convert [lng, lat] to Leaflet [lat, lng]
      const latLngs = geojsonCoords.map((c: [number, number]) => [c[1], c[0]]);

      // Automatically enable routes layer visibility
      setLayersVisibility((prev) => ({ ...prev, routes: true }));

      import('leaflet').then((L) => {
        const map = mapInstanceRef.current;
        if (!map || !routeGroupRef.current) return;

        routeGroupRef.current.clearLayers();

        routePolylineRef.current = L.polyline(latLngs, {
          pane: 'routeDirectionsPane',
          color: isRegion ? '#2563eb' : '#059669',
          weight: 4,
          opacity: 0.85,
          dashArray: isRegion ? '6, 8' : undefined
        });
        routeGroupRef.current.addLayer(routePolylineRef.current);

        map.fitBounds(routePolylineRef.current.getBounds(), { padding: [40, 40] });
      });

      setActiveRoute({
        destinationId: point.id,
        destinationTitle: point.title,
        destinationType: isRegion ? 'SOURCING_REGION' : 'MANUFACTURER',
        isRegion,
        distanceKm: Math.round(distanceMeters / 100) / 10,
        durationMinutes: Math.round(durationSeconds / 60)
      });
    } catch (err: any) {
      console.warn('[ROUTING] Routing calculation note:', err);
      setRoutingError('Directions unavailable — routing service is not configured or reachable.');
      setActiveRoute(null);
    } finally {
      setIsRouting(false);
    }
  };

  const handleClearRoute = () => {
    if (routeGroupRef.current) {
      routeGroupRef.current.clearLayers();
    }
    routePolylineRef.current = null;
    setActiveRoute(null);
    setRoutingError(null);
    setLayersVisibility((prev) => ({ ...prev, routes: false }));
  };

  return (
    <div id="sourcing-map-container" className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-4 sm:p-5 shadow-sm space-y-3">
      {/* Sourcing Header & Action Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-2 border-b border-surface-container-high">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Compass className="w-4 h-4 text-primary" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm sm:text-base font-bold text-on-surface font-mono uppercase tracking-tight">
                India Hybrid GIS Sourcing Matrix
              </h3>
              <span className="font-mono text-[10px] text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded font-semibold">
                {points.length} Sourcing Options
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-mono">
              Layered GIS: Government Administrative Context + Operational Logistics + Procurement Intelligence
            </p>
          </div>
        </div>

        {/* Live Location & Mode Indicator */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleUseMyLocation}
            disabled={isLocating}
            className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-mono font-semibold rounded-DEFAULT border border-outline-variant flex items-center gap-1.5 transition shadow-sm disabled:opacity-50"
            title="Acquire device location on demand (never continuously tracked)"
          >
            {isLocating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" />
                <span>Locating...</span>
              </>
            ) : (
              <>
                <Crosshair className="w-3.5 h-3.5 text-primary" />
                <span>{userLocation ? 'Update Location' : 'Use My Location'}</span>
              </>
            )}
          </button>

          {/* Layer Control Toggle Button */}
          <button
            type="button"
            onClick={() => setIsLayersPanelOpen(!isLayersPanelOpen)}
            className={`px-3 py-1.5 text-xs font-mono font-semibold rounded-DEFAULT border flex items-center gap-1.5 transition shadow-sm ${
              isLayersPanelOpen
                ? 'bg-primary text-on-primary border-primary'
                : 'bg-surface-container hover:bg-surface-container-high text-on-surface border-outline-variant'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>GIS Controls</span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-white/20 uppercase font-mono">
              {mapMode}
            </span>
          </button>
        </div>
      </div>

      {/* Small Map Provider Status Indicator */}
      <div className="flex items-center justify-between px-3 py-1.5 rounded-DEFAULT bg-surface-container border border-surface-container-high text-xs font-mono">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-primary shrink-0" />
          <span className="font-semibold text-on-surface">
            {getRenderedMapStatus(mapProvider, !!mapProvider.error)}
          </span>
        </div>
        <span className="text-[10px] text-secondary font-semibold uppercase tracking-wider">
          {mapProvider.isOfficialGovSource && mapProvider.availabilityState === 'ACTIVE' && !mapProvider.error
            ? 'AUTHORITATIVE GOV.IN'
            : mapProvider.availabilityState === 'DEVELOPMENT_FALLBACK'
            ? 'DEVELOPMENT ONLY'
            : 'CREDENTIALS REQUIRED'}
        </span>
      </div>

      {/* Official Government Map Provider Status Banner */}
      {mapProvider.isOfficialGovSource && mapProvider.availabilityState === 'ACTIVE' ? (
        <div className="p-2.5 rounded-DEFAULT bg-emerald-50 border border-emerald-300 text-emerald-950 text-xs flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-700 flex-shrink-0" />
            <span>
              <strong>Government of India Map Source:</strong> {mapProvider.name} &bull; Layer:{' '}
              <span className="font-semibold text-emerald-800">{mapProvider.layerName}</span>
            </span>
          </div>
          <span className="text-[10px] font-bold tracking-wider text-emerald-800 bg-emerald-200/80 px-2 py-0.5 rounded">
            AUTHORITATIVE GOV.IN
          </span>
        </div>
      ) : (
        <div className="p-2.5 rounded-DEFAULT bg-amber-50 border border-amber-300 text-amber-950 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 font-mono">
          <div className="flex items-start sm:items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-700 flex-shrink-0 mt-0.5 sm:mt-0" />
            <div>
              <span className="font-semibold block sm:inline">Map Provider Notice: </span>
              <span className="text-[11px] text-amber-900">{mapProvider.statusMessage}</span>
            </div>
          </div>
          <span className="text-[10px] font-bold tracking-wider text-amber-900 bg-amber-200/80 px-2 py-0.5 rounded self-start sm:self-auto uppercase whitespace-nowrap">
            {MAP_FALLBACK_LABEL}
          </span>
        </div>
      )}

      {mapProvider.error && (
        <div className="p-2.5 rounded-DEFAULT bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-2 font-mono">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block">Map Service Notice</span>
            <span>{mapProvider.error}</span>
          </div>
        </div>
      )}

      {/* Location Status / Error Banners */}
      {locationStatus && (
        <div className="p-2 rounded-DEFAULT bg-sky-50 border border-sky-200 text-sky-900 text-xs flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-sky-600 flex-shrink-0" />
            <span>{locationStatus}</span>
          </div>
          <span className="text-[10px] text-sky-700">Origin: Live User GPS</span>
        </div>
      )}

      {locationError && (
        <div className="p-2.5 rounded-DEFAULT bg-rose-50 border border-rose-200 text-rose-900 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block">Location Notice</span>
            <span>{locationError}</span>
          </div>
          <button
            type="button"
            onClick={() => setLocationError(null)}
            className="text-rose-500 hover:text-rose-800"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {routingError && (
        <div className="p-2.5 rounded-DEFAULT bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-semibold block">Routing Notice</span>
            <span>{routingError}</span>
          </div>
          <button
            type="button"
            onClick={() => setRoutingError(null)}
            className="text-amber-500 hover:text-amber-800"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Selected Sourcing Destination & Directions Toolbar */}
      {selectedPoint && (
        <div className="p-3 bg-surface-container-low rounded-DEFAULT border border-surface-container-high flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] font-bold px-2 py-0.5 rounded-DEFAULT bg-surface-container text-on-surface border border-surface-container-high uppercase">
                Selected Destination
              </span>
              <span className="font-bold text-on-surface font-mono">{selectedPoint.title}</span>
            </div>
            <p className="text-[11px] text-secondary">
              📍 {selectedPoint.location}
              {selectedPoint.source_type === 'SOURCING_REGION' && (
                <span className="text-primary font-semibold ml-1.5">
                  &bull; Representative corridor coordinate
                </span>
              )}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => handleGetDirections(selectedPoint)}
              disabled={isRouting}
              className="px-3.5 py-1.5 bg-primary hover:bg-primary-container text-on-primary text-xs font-mono font-semibold rounded-DEFAULT flex items-center gap-1.5 transition shadow-sm disabled:opacity-50"
            >
              {isRouting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-on-primary" />
                  <span>Routing...</span>
                </>
              ) : (
                <>
                  <Navigation className="w-3.5 h-3.5" />
                  <span>Directions</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Active Route Summary Card */}
      {activeRoute && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-DEFAULT text-emerald-950 text-xs space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2">
              <Route className="w-4 h-4 text-emerald-700" />
              <span className="font-bold font-mono">
                Driving Route to {activeRoute.destinationTitle}
              </span>
            </div>
            <button
              type="button"
              onClick={handleClearRoute}
              className="text-emerald-700 hover:text-emerald-900 font-mono text-[11px] flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" />
              <span>Clear Route</span>
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1 font-mono text-xs">
            <div className="bg-white/80 p-2 rounded-DEFAULT border border-emerald-200">
              <span className="text-[10px] text-emerald-700 block">Distance</span>
              <span className="font-bold text-sm text-emerald-900">{activeRoute.distanceKm} km</span>
            </div>
            <div className="bg-white/80 p-2 rounded-DEFAULT border border-emerald-200">
              <span className="text-[10px] text-emerald-700 block">Estimated Driving Time</span>
              <span className="font-bold text-sm text-emerald-900">
                {Math.floor(activeRoute.durationMinutes / 60)}h {activeRoute.durationMinutes % 60}m
              </span>
            </div>
            <div className="bg-white/80 p-2 rounded-DEFAULT border border-emerald-200 col-span-2 sm:col-span-1">
              <span className="text-[10px] text-emerald-700 block">Destination Type</span>
              <span className="font-bold text-xs text-emerald-900">
                {activeRoute.isRegion ? 'Region Cluster' : 'Manufacturing Site'}
              </span>
            </div>
          </div>

          {activeRoute.isRegion ? (
            <p className="text-[11px] text-emerald-800 leading-relaxed italic">
              <strong>Corridor Disclaimer:</strong> Route navigates to the representative geographic cluster center of this industrial zone. Specific factory gate addresses must be coordinated with the vendor.
            </p>
          ) : (
            <p className="text-[11px] text-emerald-800 leading-relaxed">
              Route calculated via the OpenStreetMap OSRM live routing engine. Real-time road restrictions and traffic may vary.
            </p>
          )}
        </div>
      )}

      {/* Main Leaflet Map Canvas with Embedded Floating GIS Layer Controls */}
      <div className="w-full h-[450px] bg-slate-900 rounded-DEFAULT border border-surface-container-high overflow-hidden relative shadow-inner">
        {/* The Leaflet Container */}
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Top-Right Compact GIS Layer Control Panel */}
        {isLayersPanelOpen && (
          <div className="absolute top-3 right-3 z-[1000] w-72 bg-slate-900/95 backdrop-blur-md border border-slate-700 text-slate-100 p-3.5 rounded shadow-2xl space-y-3 font-mono text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-slate-700">
              <div className="flex items-center gap-1.5">
                <SlidersHorizontal className="w-4 h-4 text-sky-400" />
                <span className="font-bold text-slate-200 uppercase tracking-tight">GIS Layers & Modes</span>
              </div>
              <button
                type="button"
                onClick={() => setIsLayersPanelOpen(false)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Mode Selector */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Map Mode
              </span>
              <div className="grid grid-cols-1 gap-1">
                <button
                  type="button"
                  onClick={() => handleModeChange('HYBRID')}
                  className={`px-2.5 py-1.5 rounded text-left text-xs flex items-center justify-between transition ${
                    mapMode === 'HYBRID'
                      ? 'bg-sky-600 text-white font-bold'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span>Hybrid GIS (Default)</span>
                  <span className="text-[10px] opacity-80">Gov + Logistics</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleModeChange('GOVERNMENT')}
                  className={`px-2.5 py-1.5 rounded text-left text-xs flex items-center justify-between transition ${
                    mapMode === 'GOVERNMENT'
                      ? 'bg-sky-600 text-white font-bold'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span>Government / Bharat Maps</span>
                  <span className="text-[10px] opacity-80">Official Context</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleModeChange('OPERATIONAL')}
                  className={`px-2.5 py-1.5 rounded text-left text-xs flex items-center justify-between transition ${
                    mapMode === 'OPERATIONAL'
                      ? 'bg-sky-600 text-white font-bold'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  <span>Operational</span>
                  <span className="text-[10px] opacity-80">Routing & Roads</span>
                </button>
              </div>
            </div>

            {/* Layers Checklist */}
            <div className="space-y-1.5 pt-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Active Layers
              </span>
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.administrativeBoundaries}
                    onChange={() => handleToggleLayer('administrativeBoundaries')}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0"
                  />
                  <span className="text-slate-200">Administrative Boundaries</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.districtBoundaries}
                    onChange={() => handleToggleLayer('districtBoundaries')}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0"
                  />
                  <span className="text-slate-200">District Boundaries</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.roadLogistics}
                    onChange={() => handleToggleLayer('roadLogistics')}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0"
                  />
                  <span className="text-slate-200">Roads / Logistics Corridors</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.sourcingRegions}
                    onChange={() => handleToggleLayer('sourcingRegions')}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0"
                  />
                  <span className="text-slate-200">Sourcing Regions (Clusters)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.procurementSources}
                    onChange={() => handleToggleLayer('procurementSources')}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0"
                  />
                  <span className="text-slate-200">Procurement Sources (Units)</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.liveGps}
                    onChange={() => handleToggleLayer('liveGps')}
                    disabled={!userLocation}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0 disabled:opacity-40"
                  />
                  <span className={userLocation ? 'text-slate-200' : 'text-slate-500'}>
                    Live GPS {!userLocation && '(Click Locate)'}
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer hover:bg-slate-800 p-1 rounded text-[11px]">
                  <input
                    type="checkbox"
                    checked={layersVisibility.routes}
                    onChange={() => handleToggleLayer('routes')}
                    disabled={!activeRoute}
                    className="rounded bg-slate-800 border-slate-600 text-sky-500 focus:ring-0 disabled:opacity-40"
                  />
                  <span className={activeRoute ? 'text-slate-200' : 'text-slate-500'}>
                    Routes {!activeRoute && '(Click Directions)'}
                  </span>
                </label>
              </div>
            </div>
          </div>
        )}

        {/* Bottom-Left Transparent Provider Legend HUD */}
        <div className="absolute bottom-3 left-3 z-[1000] max-w-[260px] bg-slate-900/85 backdrop-blur-sm border border-slate-700/70 text-slate-200 p-2 rounded shadow-lg font-mono text-[9px] space-y-1">
          <div className="font-bold text-sky-400 uppercase tracking-wider flex items-center gap-1 text-[10px]">
            <Globe2 className="w-3 h-3 text-sky-400" />
            <span>GIS Map Provider & Attribution</span>
          </div>

          <div className="space-y-1 text-[9px] leading-tight">
            <div>
              <span className="text-slate-400 block font-semibold">BASE MAP:</span>
              <span className="text-slate-200 font-medium">
                {providerStatus.baseMapProvider}
              </span>
              {providerStatus.baseMapSubtext && (
                <span className="text-amber-400 block text-[8.5px]">
                  {providerStatus.baseMapSubtext}
                </span>
              )}
            </div>

            {providerStatus.officialLayersProvider && (
              <div>
                <span className="text-slate-400 block font-semibold">ADMINISTRATIVE CONTEXT:</span>
                <span className="text-emerald-400 font-medium">
                  {providerStatus.officialLayersProvider}
                </span>
              </div>
            )}

            {providerStatus.operationalRoutingProvider && (
              <div>
                <span className="text-slate-400 block font-semibold">OPERATIONAL ROUTING:</span>
                <span className="text-sky-300 font-medium">
                  {providerStatus.operationalRoutingProvider}
                </span>
              </div>
            )}

            <div>
              <span className="text-slate-400 block font-semibold">PROCUREMENT INTELLIGENCE:</span>
              <span className="text-slate-300">
                {providerStatus.procurementIntelligenceProvider}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Statutory Notice */}
      <div className="flex items-start gap-2 bg-surface-container-low p-2.5 rounded-DEFAULT border border-surface-container-high text-xs">
        <Info className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <p className="text-secondary text-[11px] leading-relaxed">
          <strong className="text-amber-800 font-semibold">Statutory Rule: </strong>
          Industrial regions represent geographic manufacturing clusters and are <span className="underline font-semibold text-error">NEVER</span> certified suppliers under BIS/ISO audits. Specific factory site licenses must be verified before buyer approval.
        </p>
      </div>

      {/* Tactical Legend Strip */}
      <div className="flex flex-col gap-2 pt-1 font-mono text-xs px-1">
        {/* Verification Status Legend */}
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">Status:</span>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span>
              <span className="text-on-surface-variant text-[11px]">Buyer Verified (Live)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-amber-500"></span>
              <span className="text-on-surface-variant text-[11px]">Requires Live Verification</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span>
              <span className="text-on-surface-variant text-[11px]">Region Only</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm bg-rose-500"></span>
              <span className="text-on-surface-variant text-[11px]">Unverified</span>
            </div>
          </div>

          {userLocation && (
            <div className="flex items-center gap-1.5 text-sky-700">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-pulse"></span>
              <span className="text-[11px]">Origin: Live User GPS</span>
            </div>
          )}
        </div>

        {/* Concise Layer Legend */}
        <div className="flex flex-wrap items-center gap-2 pt-1.5 border-t border-surface-container-high/60">
          <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">Layers:</span>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container text-slate-700 text-[10px]">
            <span className="w-2.5 h-0.5 bg-slate-500 inline-block"></span>
            <span className="font-semibold">ADMIN</span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container text-sky-800 text-[10px]">
            <span className="w-2.5 h-0.5 border-t border-dashed border-sky-600 inline-block"></span>
            <span className="font-semibold">LOGISTICS</span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container text-blue-700 text-[10px]">
            <span className="w-2 h-2 rounded-full border border-blue-500 bg-blue-200 inline-block"></span>
            <span className="font-semibold">REGION</span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container text-emerald-800 text-[10px]">
            <span className="w-2 h-2 rounded-sm bg-emerald-600 inline-block"></span>
            <span className="font-semibold">SOURCE</span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container text-cyan-800 text-[10px]">
            <span className="w-2 h-2 rounded-full bg-cyan-600 inline-block"></span>
            <span className="font-semibold">BUYER</span>
          </div>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-surface-container text-emerald-800 text-[10px]">
            <span className="w-2.5 h-0.5 bg-emerald-600 inline-block"></span>
            <span className="font-semibold">ROUTE</span>
          </div>
        </div>
      </div>

      {/* Footer Instructions & Provider Disclosures */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between text-[11px] text-secondary pt-1 font-mono gap-1">
        <span className="flex items-center gap-1">
          <Layers className="w-3 h-3 text-primary" />
          <span>Click any marker to inspect manufacturing capabilities, BIS license scope, and coordinates</span>
        </span>
        <span className="text-secondary font-mono">
          {mapProvider.isOfficialGovSource && mapProvider.availabilityState === 'ACTIVE'
            ? `Govt. of India Map: ${mapProvider.name} • Routing: OpenStreetMap OSRM`
            : `${MAP_FALLBACK_LABEL} • Routing: OpenStreetMap OSRM`}
        </span>
      </div>
    </div>
  );
};
