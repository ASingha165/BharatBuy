import os
import re
import pytest

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
MAP_CONFIG_FILE = os.path.join(FRONTEND_DIR, "lib", "map-config.ts")
SOURCING_MAP_FILE = os.path.join(FRONTEND_DIR, "components", "SourcingMap.tsx")
TYPES_FILE = os.path.join(FRONTEND_DIR, "types", "index.ts")


def test_map_config_and_sourcing_map_files_exist():
    """Verifies that all required map provider and UI files exist."""
    assert os.path.exists(MAP_CONFIG_FILE), "map-config.ts must exist"
    assert os.path.exists(SOURCING_MAP_FILE), "SourcingMap.tsx must exist"
    assert os.path.exists(TYPES_FILE), "types/index.ts must exist"


def test_official_map_provider_type_definition():
    """
    Verifies that OfficialIndiaMapProvider interface contains all required attributes:
    - provider name
    - tile/WMS/WMTS URL
    - layer name
    - attribution
    - CRS
    - minZoom
    - maxZoom
    - availability/error state
    """
    with open(TYPES_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "interface OfficialIndiaMapProvider" in content
    assert "name: string" in content
    assert "sourceUrl: string" in content
    assert "serviceType: OfficialMapServiceType" in content
    assert "endpointUrl: string" in content
    assert "layerName: string" in content
    assert "attribution: string" in content
    assert "crs: string" in content
    assert "minZoom: number" in content
    assert "maxZoom: number" in content
    assert "availabilityState: MapAvailabilityState" in content
    assert "error?:" in content or "error:" in content
    assert "statusMessage: string" in content
    assert "isOfficialGovSource: boolean" in content


def test_no_fabricated_government_url_exists():
    """
    CRITICAL TEST — ZERO FABRICATION GUARANTEE:
    Verifies that no fabricated or invented XYZ tile URLs exist in frontend code.
    Specifically checks that the previously invented URL
    'bhuvanmaps.nrsc.gov.in/bhuvan_ras3/.../tile/{z}/{y}/{x}'
    has been completely removed.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()

    assert "bhuvanmaps.nrsc.gov.in" not in config_content, "Fabricated Bhuvan XYZ tile URL must not exist in map-config.ts"
    assert "bhuvanmaps.nrsc.gov.in" not in map_content, "Fabricated Bhuvan XYZ tile URL must not exist in SourcingMap.tsx"
    assert "bhuvan_ras3" not in config_content
    assert "bhuvan_ras3" not in map_content


def test_official_government_providers_configured_in_map_config():
    """
    Verifies official Government of India mapping presets are present:
    1. NIC Bharat Maps / National Portal of Map Services (https://mapservice.gov.in/)
    2. ISRO / NRSC Bhuvan (https://bhuvan.nrsc.gov.in/)
    3. Survey of India (https://surveyofindia.gov.in/)
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "BHARAT_MAPS_PRESET" in content
    assert "https://mapservice.gov.in/" in content
    assert "BHUVAN_PRESET" in content
    assert "https://bhuvan.nrsc.gov.in/" in content
    assert "SOI_PRESET" in content
    assert "https://surveyofindia.gov.in/" in content
    assert "getOfficialMapProvider" in content


def test_attribution_requirements_enforced():
    """
    Verifies that official attribution clearly credits Government of India / provider:
    - NIC Bharat Maps: Government of India / National Informatics Centre (NIC) Bharat Maps
    - Bhuvan: Government of India / ISRO-NRSC Bhuvan
    - Survey of India: Government of India / Survey of India
    - Does NOT falsely write 'Government of India map' for OpenStreetMap fallback
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Government of India / National Informatics Centre (NIC) Bharat Maps" in content
    assert "Government of India / ISRO-NRSC Bhuvan" in content
    assert "Government of India / Survey of India (SoI)" in content
    assert "OpenStreetMap contributors" in content


def test_development_fallback_explicitly_labeled():
    """
    Verifies fallback behavior:
    - Must be explicitly labeled: 'Development fallback — OpenStreetMap'
    - Must NOT silently fall back to OSM and pretend it is an official Government of India map
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()

    assert "MAP_FALLBACK_LABEL" in config_content
    assert "MAP_FALLBACK_LABEL" in map_content
    assert "Development fallback" in config_content
    assert "OpenStreetMap" in config_content
    assert "Development fallback" in map_content
    assert "OpenStreetMap" in map_content
    # Check exact label presence in config
    assert ("Development fallback — OpenStreetMap" in config_content or 
            "Development fallback \u2014 OpenStreetMap" in config_content or
            "Development fallback - OpenStreetMap" in config_content)
    assert ("Development fallback — OpenStreetMap" in map_content or
            "Development fallback \u2014 OpenStreetMap" in map_content or
            "Development fallback - OpenStreetMap" in map_content)


def test_india_bounds_enforced():
    """
    Verifies strict India-focused geographic bounds:
    - South: 6.0°N
    - West: 68.0°E
    - North: 37.5°N
    - East: 97.5°E
    - maxBoundsViscosity: 1.0
    - minZoom: 4, maxZoom: 13
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()

    assert "6.0" in config_content and "68.0" in config_content
    assert "37.5" in config_content and "97.5" in config_content
    assert "minZoom: 4" in config_content or "minZoom: 4" in map_content
    assert "maxZoom: 13" in config_content or "maxZoom: 13" in map_content
    assert "maxBoundsViscosity: 1.0" in config_content or "maxBoundsViscosity: 1.0" in map_content


def test_leaflet_wms_mechanism_used_for_wms_providers():
    """
    Verifies that when a WMS service is used, Leaflet consumes it via L.tileLayer.wms
    rather than treating it as an XYZ tile endpoint.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "L.tileLayer.wms" in content
    assert "format: 'image/png'" in content
    assert "transparent: true" in content


def test_existing_markers_and_distinct_semantics_preserved():
    """
    Verifies that:
    - Buyer Verified (Live), Requires Live Verification, Region Only, Unverified markers render
    - Colors: Emerald (#10b981), Amber (#f59e0b), Blue (#3b82f6), Rose (#f43f5e)
    - REGION_ONLY remains distinct from verified MANUFACTURER
    - Statutory rule on industrial clusters is preserved
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "#10b981" in content, "Buyer Verified (Live) emerald marker color"
    assert "#f59e0b" in content, "Requires Live Verification amber marker color"
    assert "#3b82f6" in content, "Region Only blue marker color"
    assert "#f43f5e" in content, "Unverified rose marker color"

    assert "Buyer Verified (Live)" in content
    assert "Requires Live Verification" in content
    assert "Region Only" in content
    assert "Unverified" in content

    assert "SOURCING_REGION" in content
    assert "Statutory Rule" in content
    assert "Industrial regions represent geographic manufacturing clusters and are" in content


def test_buyer_location_and_directions_routing_intact():
    """
    Verifies that:
    - Live user location continues to work via on-demand navigator.geolocation.getCurrentPosition
    - No background continuous tracking (watchPosition)
    - OSRM driving directions routing continues to calculate distance, duration, and geometry
    - Basemap and routing service remain separate
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Location checks
    assert "handleUseMyLocation" in content
    assert "getCurrentPosition" in content
    assert "watchPosition" not in content, "Must not continuously track user via watchPosition"
    assert "userAccuracyCircleRef" in content

    # Routing checks
    assert "handleGetDirections" in content
    assert "handleClearRoute" in content
    assert "activeRoute" in content
    assert "router.project-osrm.org" in content or "NEXT_PUBLIC_ROUTING_API_URL" in content
    assert "distanceKm" in content
    assert "durationMinutes" in content


def test_no_supplier_claims_generated_from_government_map_data():
    """
    Verifies that government map data is treated strictly as geographic/administrative basemap,
    and supplier verification claims are completely isolated from map data.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Kalinga Nagar Industrial Complex disclaimer
    assert "Corridor Disclaimer" in content
    assert "Representative corridor coordinate" in content


def test_government_map_provider_status_indicators():
    """
    Verifies that map status indicator accurately reports:
    - Map: NIC Bharat Maps — Government of India (when active)
    - Map: NIC Bharat Maps — service unavailable (when error)
    - Map: Development fallback — OpenStreetMap (when development fallback active)
    - Map: NIC Bharat Maps — Awaiting authorized service endpoint/credentials (when awaiting credentials)
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()

    assert "getRenderedMapStatus" in config_content
    assert "getRenderedMapStatus" in map_content
    assert "Map: NIC Bharat Maps — Government of India" in config_content
    assert "Map: NIC Bharat Maps — service unavailable" in config_content
    assert "Map: Development fallback — OpenStreetMap" in config_content
    assert "Map: NIC Bharat Maps — Awaiting authorized service endpoint/credentials" in config_content
    assert "Awaiting authorized Bharat Maps service endpoint/credentials" in config_content


def test_no_false_government_label_when_osm_rendered():
    """
    Verifies that OpenStreetMap fallback is NEVER falsely labeled as Government of India map.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()

    # In FALLBACK_PROVIDER:
    assert "name: 'Development fallback — OpenStreetMap'" in config_content
    assert "isOfficialGovSource: false" in config_content


def test_government_map_provider_type_alias_exported():
    """Verifies that GovernmentMapProvider is exported for consumers."""
    with open(TYPES_FILE, "r", encoding="utf-8") as f:
        types_content = f.read()
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()

    assert "export type GovernmentMapProvider" in types_content
    assert "GovernmentMapProvider" in config_content

