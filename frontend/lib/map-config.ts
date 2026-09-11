export const OFFICIAL_MAP_TILE_URL =
  process.env.NEXT_PUBLIC_MAP_TILE_URL ||
  'https://bhuvanmaps.nrsc.gov.in/bhuvan_ras3/server/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';

export const OFFICIAL_MAP_ATTRIBUTION =
  process.env.NEXT_PUBLIC_MAP_ATTRIBUTION ||
  '&copy; <a href="https://bhuvan.nrsc.gov.in/" target="_blank" rel="noopener noreferrer">Bhuvan / ISRO-NRSC</a>, Government of India';

// Kept as a network-failure fallback only; it is never the primary provider.
export const MAP_FALLBACK_TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
export const MAP_FALLBACK_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a>';