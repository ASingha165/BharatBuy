'use client';

import React, { useEffect, useRef, useState } from 'react';
import { MapPointItem } from '../types';
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
  MapPin
} from 'lucide-react';

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
  const [isMapReady, setIsMapReady] = useState(false);

  // Live User Location State (on-demand, never continuously tracked)
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
  const routeLayerRef = useRef<any>(null);

  // Find currently selected point
  const selectedPoint = points.find((p) => p.id === selectedPointId) || null;

  // 1. Initialize Map
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
      const indiaBounds = L.latLngBounds([6.0, 68.0], [37.5, 97.5]);

      const map = L.map(mapContainerRef.current, {
        maxBounds: indiaBounds,
        maxBoundsViscosity: 1.0,
        minZoom: 4,
        maxZoom: 13,
        zoomSnap: 0.5,
        zoomControl: true,
        attributionControl: true
      });

      // OpenStreetMap basemap with visible attribution.
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        minZoom: 4,
        maxZoom: 13,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>'
      }).addTo(map);

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

  // 2. Render Markers for Sourcing Points
  useEffect(() => {
    if (!isMapReady || !mapInstanceRef.current || typeof window === 'undefined') return;

    import('leaflet').then((L) => {
      const map = mapInstanceRef.current;
      if (!map) return;

      // Clear existing markers
      Object.values(markersRef.current).forEach((marker: any) => marker.remove());
      markersRef.current = {};

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
          statusLabel = 'Unverified Source';
        }

        const markerHtml = `
          <div style="position: relative; display: flex; align-items: center; justify-content: center;">
            <div style="
              width: ${isSelected ? '24px' : '16px'};
              height: ${isSelected ? '24px' : '16px'};
              background: ${markerColor};
              border: 2px solid #ffffff;
              border-radius: ${isRegion ? '50%' : '4px'};
              box-shadow: 0 0 10px ${markerColor};
              display: flex;
              align-items: center;
              justify-content: center;
              cursor: pointer;
              transition: all 0.2s ease;
            ">
              <div style="width: 4px; height: 4px; background: white; border-radius: 50%;"></div>
            </div>
            ${isSelected ? `<div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; border: 2px solid ${markerColor}; opacity: 0.6; animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>` : ''}
          </div>
        `;

        const customIcon = L.divIcon({
          className: 'custom-leaflet-marker',
          html: markerHtml,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
          popupAnchor: [0, -16]
        });

        const marker = L.marker([point.latitude, point.longitude], { icon: customIcon }).addTo(map);

        const standardsText = point.relevant_standards && point.relevant_standards.length > 0
          ? point.relevant_standards.slice(0, 3).join(', ')
          : 'Standards Conforming';

        const evidenceHtml = point.evidence_preview && point.evidence_preview.length > 0
          ? `<div style="margin-top: 4px; padding-top: 4px; border-top: 1px dashed #cbd5e1; font-size: 10px; color: #475569;">
               <strong>Evidence:</strong> ${point.evidence_preview[0]}
             </div>`
          : '';

        const popupContent = `
          <div style="font-family: system-ui, sans-serif; font-size: 12px; color: #0f172a; padding: 4px; min-width: 220px; max-width: 270px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-size: 9px; font-weight: 700; color: ${badgeColor}; background: ${badgeBg}; padding: 2px 6px; border-radius: 3px; text-transform: uppercase; font-family: monospace;">
                ${statusLabel}
              </span>
              <span style="font-weight: 700; color: #0284c7; font-size: 11px; font-family: monospace;">
                ${Math.round(point.suitability_score * 100)}% Match
              </span>
            </div>
            <div style="font-weight: 700; font-size: 13px; color: #0f172a; margin-bottom: 2px;">
              ${point.title}
            </div>
            <div style="font-size: 11px; color: #64748b; margin-bottom: 5px;">
              📍 ${point.location}
            </div>
            <div style="font-size: 11px; margin-bottom: 3px;">
              <strong style="color: #334155;">Items:</strong> ${point.supported_items.slice(0, 2).join(', ')}
            </div>
            <div style="font-size: 11px; margin-bottom: 3px;">
              <strong style="color: #334155;">Standards:</strong> <span style="font-family: monospace; color: #b45309;">${standardsText}</span>
            </div>
            ${evidenceHtml}
            <div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid #e2e8f0; font-size: 10px; color: #64748b; text-align: center;">
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

  // 3. Handle Live Geolocation (On-Demand only)
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

        import('leaflet').then((L) => {
          const map = mapInstanceRef.current;
          if (!map) return;

          if (userMarkerRef.current) userMarkerRef.current.remove();
          if (userAccuracyCircleRef.current) userAccuracyCircleRef.current.remove();

          // User accuracy circle
          userAccuracyCircleRef.current = L.circle([latitude, longitude], {
            radius: accuracy,
            color: '#0284c7',
            fillColor: '#38bdf8',
            fillOpacity: 0.15,
            weight: 1.5
          }).addTo(map);

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

          userMarkerRef.current = L.marker([latitude, longitude], { icon: userIcon })
            .addTo(map)
            .bindPopup(`
              <div style="font-family: system-ui, sans-serif; font-size: 12px; color: #0f172a; padding: 4px;">
                <div style="font-weight: 700; color: #0284c7; margin-bottom: 2px;">📍 Your Current Location</div>
                <div style="font-size: 10px; color: #64748b;">Accuracy: &plusmn;${Math.round(accuracy)} meters</div>
                <div style="font-size: 10px; color: #334155; margin-top: 3px;">Starting point for sourcing navigation</div>
              </div>
            `);

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

  // 4. Calculate Driving Directions via OSRM
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

      import('leaflet').then((L) => {
        const map = mapInstanceRef.current;
        if (!map) return;

        if (routeLayerRef.current) {
          routeLayerRef.current.remove();
        }

        routeLayerRef.current = L.polyline(latLngs, {
          color: isRegion ? '#2563eb' : '#059669',
          weight: 4,
          opacity: 0.85,
          dashArray: isRegion ? '6, 8' : undefined
        }).addTo(map);

        map.fitBounds(routeLayerRef.current.getBounds(), { padding: [40, 40] });
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
    if (routeLayerRef.current) {
      routeLayerRef.current.remove();
      routeLayerRef.current = null;
    }
    setActiveRoute(null);
    setRoutingError(null);
  };

  return (
    <div id="sourcing-map-container" className="bg-surface-container-lowest border border-surface-container-high rounded-DEFAULT p-5 shadow-sm space-y-3">
      {/* Sourcing Header & Action Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-surface-container-high">
        <div className="flex items-center gap-2">
          <Radar className="w-4 h-4 text-primary" />
          <h3 className="text-sm sm:text-base font-bold text-on-surface font-mono uppercase tracking-tight">
            Geographic Source Matrix & Manufacturing Map
          </h3>
          <span className="font-mono text-[10px] text-primary bg-surface-container border border-surface-container-high px-2 py-0.5 rounded-DEFAULT font-semibold">
            {points.length} Sourcing Options
          </span>
        </div>

        {/* Live Location Action Button */}
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleUseMyLocation}
            disabled={isLocating}
            className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-mono font-semibold rounded-DEFAULT border border-outline-variant flex items-center gap-1.5 transition shadow-sm disabled:opacity-50"
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
        </div>
      </div>

      {/* Location Status / Error Banners */}
      {locationStatus && (
        <div className="p-2 rounded-DEFAULT bg-sky-50 border border-sky-200 text-sky-900 text-xs flex items-center justify-between font-mono">
          <div className="flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-sky-600 flex-shrink-0" />
            <span>{locationStatus}</span>
          </div>
          <span className="text-[10px] text-sky-700">Live GPS</span>
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

      {/* Mandatory Statutory Notice */}
      <div className="flex items-start gap-2 bg-surface-container-low p-2.5 rounded-DEFAULT border border-surface-container-high text-xs">
        <Info className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <p className="text-secondary text-[11px] leading-relaxed">
          <strong className="text-amber-800 font-semibold">Statutory Rule: </strong>
          Industrial regions represent geographic manufacturing clusters and are <span className="underline font-semibold text-error">NEVER</span> certified suppliers under BIS/ISO audits. Specific factory site licenses must be verified before buyer approval.
        </p>
      </div>

      {/* Tactical Legend Strip */}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-mono px-1">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-DEFAULT bg-emerald-500"></span>
            <span className="text-on-surface-variant text-[11px]">Buyer Verified (Live)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-DEFAULT bg-amber-500"></span>
            <span className="text-on-surface-variant text-[11px]">Requires Live Verification</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-primary"></span>
            <span className="text-on-surface-variant text-[11px]">Region Only</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-DEFAULT bg-error"></span>
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

      {/* Interactive Leaflet Map Canvas */}
      <div className="w-full h-[380px] bg-surface-container-low rounded-DEFAULT border border-surface-container-high overflow-hidden relative shadow-inner">
        <div ref={mapContainerRef} className="w-full h-full" />
      </div>

      {/* Footer Instructions */}
      <div className="flex items-center justify-between text-[11px] text-secondary pt-1 font-mono">
        <span className="flex items-center gap-1">
          <Layers className="w-3 h-3 text-primary" />
          <span>Click any marker to inspect manufacturing capabilities, BIS license scope, and coordinates</span>
        </span>
        <span className="hidden sm:inline text-secondary font-mono">
          OpenStreetMap Basemap &bull; OpenStreetMap OSRM Routing
        </span>
      </div>
    </div>
  );
};
