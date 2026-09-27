import {
  OfficialIndiaMapProvider,
  GovernmentMapProvider,
  GisMapMode,
  GisLayerVisibility,
  GisProviderStatus
} from '../types';

export type { GovernmentMapProvider, GisMapMode, GisLayerVisibility, GisProviderStatus };

/**
 * Official Government of India Geospatial Mapping Services Configuration
 * 
 * Preferred Authoritative Sources:
 * 1. NIC Bharat Maps / National Portal of Map Services (https://mapservice.gov.in/)
 * 2. Survey of India official mapping services (https://surveyofindia.gov.in/)
 * 3. ISRO / NRSC Bhuvan Geo-Platform (https://bhuvan.nrsc.gov.in/)
 * 
 * CRITICAL ZERO-FABRICATION RULE:
 * - We NEVER invent XYZ tile URLs or fabricate endpoints.
 * - Mapservice.gov.in, Survey of India, and Bhuvan require authorized onboarding
 *   and credentials for direct application integration.
 * - In development environments where credentials are not yet provisioned, a configurable
 *   fallback is provided, strictly and visibly labeled:
 *   "Development fallback — OpenStreetMap"
 * - Production deployments require configured authorized Government of India credentials.
 * - NEXT_PUBLIC_ENABLE_MAP_FALLBACK=false is the production default.
 */

export const INDIA_MAP_BOUNDS = {
  south: 6.0,
  west: 68.0,
  north: 37.5,
  east: 97.5,
  minZoom: 4,
  maxZoom: 13,
  maxBoundsViscosity: 1.0
};

export const BHARAT_MAPS_PRESET: Omit<OfficialIndiaMapProvider, 'endpointUrl' | 'layerName' | 'availabilityState' | 'statusMessage'> = {
  name: 'NIC Bharat Maps — Government of India',
  sourceUrl: 'https://mapservice.gov.in/',
  serviceType: 'WMS',
  attribution: 'NIC Bharat Maps — Government of India &copy; Government of India / National Informatics Centre (NIC) Bharat Maps &copy; <a href="https://mapservice.gov.in/" target="_blank" rel="noopener noreferrer">NIC Bharat Maps</a>',
  crs: 'EPSG:3857',
  minZoom: INDIA_MAP_BOUNDS.minZoom,
  maxZoom: INDIA_MAP_BOUNDS.maxZoom,
  requiresCredentials: true,
  isOfficialGovSource: true
};

export const BHUVAN_PRESET: Omit<OfficialIndiaMapProvider, 'endpointUrl' | 'layerName' | 'availabilityState' | 'statusMessage'> = {
  name: 'ISRO / NRSC Bhuvan — Government of India',
  sourceUrl: 'https://bhuvan.nrsc.gov.in/',
  serviceType: 'WMS',
  attribution: 'Map data: Government of India / ISRO-NRSC Bhuvan &copy; <a href="https://bhuvan.nrsc.gov.in/" target="_blank" rel="noopener noreferrer">Bhuvan / ISRO</a>',
  crs: 'EPSG:4326',
  minZoom: INDIA_MAP_BOUNDS.minZoom,
  maxZoom: INDIA_MAP_BOUNDS.maxZoom,
  requiresCredentials: true,
  isOfficialGovSource: true
};

export const SOI_PRESET: Omit<OfficialIndiaMapProvider, 'endpointUrl' | 'layerName' | 'availabilityState' | 'statusMessage'> = {
  name: 'Survey of India (SoI) — Government of India',
  sourceUrl: 'https://surveyofindia.gov.in/',
  serviceType: 'WMS',
  attribution: 'Map data: Government of India / Survey of India (SoI) &copy; <a href="https://surveyofindia.gov.in/" target="_blank" rel="noopener noreferrer">Survey of India</a>',
  crs: 'EPSG:3857',
  minZoom: INDIA_MAP_BOUNDS.minZoom,
  maxZoom: INDIA_MAP_BOUNDS.maxZoom,
  requiresCredentials: true,
  isOfficialGovSource: true
};

export const MAP_FALLBACK_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
export const MAP_FALLBACK_ATTRIBUTION =
  'Development map fallback — OpenStreetMap &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>';
export const MAP_FALLBACK_LABEL = 'Development fallback — OpenStreetMap';

export const FALLBACK_PROVIDER: OfficialIndiaMapProvider = {
  name: 'Development fallback — OpenStreetMap',
  sourceUrl: 'https://www.openstreetmap.org/',
  serviceType: 'XYZ',
  endpointUrl: MAP_FALLBACK_TILE_URL,
  layerName: 'standard',
  attribution: MAP_FALLBACK_ATTRIBUTION,
  crs: 'EPSG:3857',
  minZoom: INDIA_MAP_BOUNDS.minZoom,
  maxZoom: INDIA_MAP_BOUNDS.maxZoom,
  requiresCredentials: false,
  availabilityState: 'DEVELOPMENT_FALLBACK',
  statusMessage: 'Development fallback — OpenStreetMap',
  isOfficialGovSource: false
};

// Export legacy constants for backward compatibility without fabricated URLs
export const OFFICIAL_MAP_TILE_URL = process.env.NEXT_PUBLIC_GOV_MAP_URL || '';
export const OFFICIAL_MAP_ATTRIBUTION = BHARAT_MAPS_PRESET.attribution;

/**
 * Checks whether development map fallback is explicitly enabled.
 * Production default is false.
 */
export function isMapFallbackEnabled(): boolean {
  const envVal = (process.env.NEXT_PUBLIC_ENABLE_MAP_FALLBACK || '').trim().toLowerCase();
  return envVal === 'true' || envVal === '1';
}

export function getOfficialMapProvider(): OfficialIndiaMapProvider {
  // Check for explicitly configured Government of India endpoint
  const govUrl = (process.env.NEXT_PUBLIC_GOV_MAP_URL || '').trim();
  const govLayer = (process.env.NEXT_PUBLIC_GOV_MAP_LAYER || 'NICMAPS_BaseMap').trim();
  const providerKey = (process.env.NEXT_PUBLIC_MAP_PROVIDER || 'bharatmaps').trim().toLowerCase();
  const fallbackEnabled = isMapFallbackEnabled();

  if (govUrl) {
    let preset = BHARAT_MAPS_PRESET;
    if (providerKey === 'bhuvan') {
      preset = BHUVAN_PRESET;
    } else if (providerKey === 'soi' || providerKey === 'surveyofindia') {
      preset = SOI_PRESET;
    }

    return {
      ...preset,
      endpointUrl: govUrl,
      layerName: govLayer,
      availabilityState: 'ACTIVE',
      statusMessage: `Official Government of India mapping layer active (${preset.name})`,
      error: null
    };
  }

  // When no official government endpoint is provisioned:
  if (fallbackEnabled) {
    return {
      ...FALLBACK_PROVIDER,
      statusMessage: 'Development fallback — OpenStreetMap'
    };
  }

  let selectedPreset = BHARAT_MAPS_PRESET;
  if (providerKey === 'bhuvan') {
    selectedPreset = BHUVAN_PRESET;
  } else if (providerKey === 'soi' || providerKey === 'surveyofindia') {
    selectedPreset = SOI_PRESET;
  }

  return {
    ...selectedPreset,
    endpointUrl: '',
    layerName: '',
    availabilityState: 'CREDENTIALS_REQUIRED',
    statusMessage: 'Awaiting authorized Bharat Maps service endpoint/credentials',
    error: 'Unconfigured Government of India map service. Onboarding required at mapservice.gov.in.'
  };
}

/**
 * Returns formatted map-provider status text that strictly reflects the actual rendered basemap.
 * Never reports a government map merely because configured provider name is 'bharatmaps'.
 */
export function getRenderedMapStatus(provider: OfficialIndiaMapProvider, hasError: boolean = false): string {
  if (provider.isOfficialGovSource && provider.availabilityState === 'ACTIVE' && !hasError) {
    if (provider.name.includes('Bhuvan')) {
      return 'Map: ISRO Bhuvan — Government of India';
    }
    if (provider.name.includes('Survey of India')) {
      return 'Map: Survey of India — Government of India';
    }
    return 'Map: NIC Bharat Maps — Government of India';
  }

  if (provider.isOfficialGovSource && (hasError || provider.availabilityState === 'UNAVAILABLE')) {
    return 'Map: NIC Bharat Maps — service unavailable';
  }

  if (provider.availabilityState === 'DEVELOPMENT_FALLBACK' || !provider.isOfficialGovSource) {
    return 'Map: Development fallback — OpenStreetMap';
  }

  if (provider.availabilityState === 'CREDENTIALS_REQUIRED') {
    return 'Map: NIC Bharat Maps — Awaiting authorized service endpoint/credentials';
  }

  return `Map: ${provider.name}`;
}

// ==============================================================================
// GIS HYBRID / MIXED MAP ARCHITECTURE CONFIGURATION
// ==============================================================================

export const DEFAULT_GIS_MODE: GisMapMode = 'HYBRID';

export const DEFAULT_LAYER_VISIBILITY: GisLayerVisibility = {
  administrativeBoundaries: true,
  districtBoundaries: true,
  roadLogistics: true,
  sourcingRegions: true,
  procurementSources: true,
  liveGps: false,
  routes: false
};

/**
 * Returns the default layer visibility settings when a user switches map modes.
 */
export function getLayerConfigurationForMode(
  mode: GisMapMode,
  currentVisibility: GisLayerVisibility = DEFAULT_LAYER_VISIBILITY
): GisLayerVisibility {
  switch (mode) {
    case 'GOVERNMENT':
      return {
        ...currentVisibility,
        administrativeBoundaries: true,
        districtBoundaries: true,
        roadLogistics: false,
        sourcingRegions: true,
        procurementSources: true
      };
    case 'HYBRID':
      return {
        ...currentVisibility,
        administrativeBoundaries: true,
        districtBoundaries: true,
        roadLogistics: true,
        sourcingRegions: true,
        procurementSources: true
      };
    case 'OPERATIONAL':
      return {
        ...currentVisibility,
        administrativeBoundaries: false,
        districtBoundaries: false,
        roadLogistics: true,
        sourcingRegions: true,
        procurementSources: true
      };
    default:
      return DEFAULT_LAYER_VISIBILITY;
  }
}

/**
 * Returns structured provider legend information based on active map mode, provider, and active layers.
 * Strict honest attribution: only includes providers that are actually active/rendered.
 */
export function getGisProviderStatus(
  provider: OfficialIndiaMapProvider,
  mode: GisMapMode,
  layers: GisLayerVisibility,
  isRouteActive: boolean
): GisProviderStatus {
  const isGovActive = provider.isOfficialGovSource && provider.availabilityState === 'ACTIVE' && !provider.error;
  const isFallback = provider.availabilityState === 'DEVELOPMENT_FALLBACK';

  let baseMapProvider = 'Government map service not configured';
  let baseMapSubtext: string | undefined = undefined;

  if (isGovActive) {
    baseMapProvider = provider.name;
  } else if (isFallback) {
    baseMapProvider = 'Government map service not configured';
    baseMapSubtext = 'Development fallback — OpenStreetMap';
  } else {
    baseMapProvider = 'Government map service not configured (Onboarding required at mapservice.gov.in)';
  }

  // Administrative Context Layer (BharatBuy static GIS dataset vs live Gov WMS)
  let officialLayersProvider: string | null = null;
  if (isGovActive) {
    officialLayersProvider = `${provider.name} (Live Official Administrative Layers)`;
  } else if (layers.administrativeBoundaries || layers.districtBoundaries) {
    officialLayersProvider = 'Administrative context — BharatBuy static GIS dataset';
  }

  // Operational Routing & Road logistics (OSM / OSRM)
  let operationalRoutingProvider: string | null = null;
  if (layers.roadLogistics || layers.routes || isRouteActive || mode === 'OPERATIONAL') {
    operationalRoutingProvider = 'OpenStreetMap / OSRM (Operational Logistics & Routing)';
  }

  return {
    baseMapProvider,
    baseMapSubtext,
    isFallback,
    officialLayersProvider,
    operationalRoutingProvider,
    procurementIntelligenceProvider: 'BharatBuy AI Procurement Matrix'
  };
}