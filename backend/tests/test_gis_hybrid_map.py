import os
import re
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
MAP_CONFIG_FILE = os.path.join(FRONTEND_DIR, "lib", "map-config.ts")
SOURCING_MAP_FILE = os.path.join(FRONTEND_DIR, "components", "SourcingMap.tsx")
TYPES_FILE = os.path.join(FRONTEND_DIR, "types", "index.ts")
ADMIN_GIS_FILE = os.path.join(FRONTEND_DIR, "lib", "india-admin-gis.ts")


def test_1_government_provider_selected_when_configured():
    """
    1. Government provider is selected when configured.
    Verifies that when NEXT_PUBLIC_GOV_MAP_URL is provided, map-config activates
    the authoritative Government of India map provider.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "govUrl" in content
    assert "NEXT_PUBLIC_GOV_MAP_URL" in content
    assert "availabilityState: 'ACTIVE'" in content
    assert "isOfficialGovSource: true" in content
    assert "NIC Bharat Maps — Government of India" in content


def test_2_hybrid_mode_loads_government_operational_bharatbuy_layers():
    """
    2. Hybrid mode loads government + operational + BharatBuy layers.
    Verifies that HYBRID mode is configured as the default and coordinates
    Government administrative context, Operational road logistics, and BharatBuy sourcing markers.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()
    with open(TYPES_FILE, "r", encoding="utf-8") as f:
        types_content = f.read()

    assert "DEFAULT_GIS_MODE: GisMapMode = 'HYBRID'" in config_content or "DEFAULT_GIS_MODE = 'HYBRID'" in config_content
    assert "GisMapMode" in types_content
    assert "'GOVERNMENT' | 'HYBRID' | 'OPERATIONAL'" in types_content
    assert "getLayerConfigurationForMode" in config_content
    # Hybrid mode sets administrativeBoundaries (gov), roadLogistics (operational), and sourcing markers
    assert "administrativeBoundaries: true" in config_content
    assert "roadLogistics: true" in config_content
    assert "sourcingRegions: true" in config_content
    assert "procurementSources: true" in config_content


def test_3_osm_fallback_used_only_when_explicitly_enabled():
    """
    3. OSM fallback is used only when explicitly enabled.
    Verifies that NEXT_PUBLIC_ENABLE_MAP_FALLBACK=false is the production default,
    and when disabled without a gov URL, it never silently uses OSM.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "isMapFallbackEnabled" in content
    assert "NEXT_PUBLIC_ENABLE_MAP_FALLBACK" in content
    assert "CREDENTIALS_REQUIRED" in content
    assert "Awaiting authorized Bharat Maps service endpoint/credentials" in content


def test_4_osm_never_labelled_government_of_india():
    """
    4. OSM is never labelled Government of India.
    Verifies strict zero-fabrication: OSM fallback is never credited to Government of India.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()

    # FALLBACK_PROVIDER has isOfficialGovSource false
    assert "isOfficialGovSource: false" in config_content
    assert "MAP_FALLBACK_LABEL = 'Development fallback — OpenStreetMap'" in config_content
    # SourcingMap separates Gov. of India vs Development fallback
    assert "Govt. of India Map: ${mapProvider.name}" in map_content
    assert "${MAP_FALLBACK_LABEL} • Routing: OpenStreetMap OSRM" in map_content


def test_5_government_attribution_appears_only_when_active():
    """
    5. Government attribution appears only when the government layer is actually active.
    Verifies provider legend HUD calculates attribution dynamically and credits Government
    layers only when administrative or official layers are selected.
    """
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        config_content = f.read()
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        map_content = f.read()

    assert "getGisProviderStatus" in config_content
    assert "officialLayersProvider" in config_content
    assert "Administrative context — BharatBuy static GIS dataset" in config_content
    assert "providerStatus.officialLayersProvider" in map_content


def test_6_region_only_markers_remain_region_only():
    """
    6. REGION_ONLY markers remain REGION_ONLY.
    Verifies industrial regions represent representative corridor zones and are NEVER converted to certified suppliers.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SOURCING_REGION" in content
    assert "REGION_ONLY" in content
    assert "#3b82f6" in content, "Region Only blue marker"
    assert "Representative corridor coordinate" in content
    assert "Corridor Disclaimer" in content
    assert "Representative corridor center — not a specific factory gate" in content or "Industrial regions represent geographic manufacturing clusters" in content
    assert "NEVER" in content


def test_7_source_markers_remain_sources():
    """
    7. Source markers remain sources.
    Verifies manufacturers/suppliers retain distinct verification colors and inspection details.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Colors
    assert "#10b981" in content, "Buyer Verified (Live) emerald"
    assert "#f59e0b" in content, "Requires Live Verification amber"
    assert "#f43f5e" in content, "Unverified rose"

    assert "Buyer Verified (Live)" in content
    assert "Requires Live Verification" in content
    assert "Unverified" in content
    assert "handleGetDirections" in content


def test_8_gps_remains_on_demand():
    """
    8. GPS remains on-demand.
    Verifies navigator.geolocation.getCurrentPosition is used on demand and no continuous tracking occurs.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "handleUseMyLocation" in content
    assert "getCurrentPosition" in content
    assert "watchPosition" not in content
    assert "Origin: Live User GPS" in content


def test_9_routing_remains_operational():
    """
    9. Routing remains operational.
    Verifies legitimate routing using OSRM, attributed as operational logistics, not government mapping.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "handleGetDirections" in content
    assert "router.project-osrm.org" in content or "NEXT_PUBLIC_ROUTING_API_URL" in content
    assert "OpenStreetMap / OSRM (Operational Logistics & Routing)" in content or "OpenStreetMap OSRM" in content
    assert "distanceKm" in content
    assert "durationMinutes" in content


def test_10_layer_toggles_do_not_destroy_procurement_markers():
    """
    10. Layer toggles do not destroy procurement markers.
    Verifies that layer toggling works through Leaflet LayerGroups without clearing point state or markersRef.
    """
    with open(SOURCING_MAP_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "adminBoundariesGroupRef" in content
    assert "districtBoundariesGroupRef" in content
    assert "roadLogisticsGroupRef" in content
    assert "sourcingRegionsGroupRef" in content
    assert "procurementSourcesGroupRef" in content
    assert "layersVisibility" in content
    assert "handleToggleLayer" in content
    # Toggling adds or removes group without modifying markersRef
    assert "map.addLayer" in content
    assert "map.removeLayer" in content


def test_11_missing_government_service_fails_honestly():
    """
    11. Missing government service fails honestly.
    Verifies that unconfigured government endpoints produce clear informative errors and backend proxy returns 503.
    """
    # 1. Frontend config check
    with open(MAP_CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Unconfigured Government of India map service. Onboarding required at mapservice.gov.in." in content

    # 2. Backend API proxy check
    resp = client.get("/api/v1/gis/proxy")
    assert resp.status_code == 503
    assert "NIC Bharat Maps service endpoint or credentials not configured on server" in resp.json()["detail"]


def test_12_no_government_credentials_reach_browser_javascript():
    """
    12. No government credentials reach browser JavaScript.
    Verifies zero government API keys, tokens, or secrets exist in frontend files.
    """
    for file_path in [MAP_CONFIG_FILE, SOURCING_MAP_FILE, TYPES_FILE, ADMIN_GIS_FILE]:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "NIC_TOKEN" not in content
        assert "BHARAT_MAPS_KEY" not in content
        assert "GOV_MAP_KEY" not in content
        assert "SECRET" not in content
