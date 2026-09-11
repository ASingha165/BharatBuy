from typing import Dict, Any, List
from backend.app.services.preprocessing_service import PreprocessingService

PRODUCT_CATEGORIES = {
    "cable": ["cable", "cables", "conductor", "conductors", "wire", "wires", "cord", "cords"],
    "transformer": ["transformer", "transformers", "substation"],
    "pipe": ["pipe", "pipes", "tubing", "conduit", "pipeline"],
    "steel": ["steel", "rebar", "structural steel", "iron"],
    "cement": ["cement", "concrete", "mortar"],
    "switchgear": ["switchgear", "circuit breaker", "fuse", "relay", "panel"],
    "valve": ["valve", "valves", "fitting"],
    "meter": ["meter", "energy meter", "voltmeter", "ammeter"]
}

MATERIAL_TYPES = {
    "pvc": ["pvc", "polyvinyl chloride"],
    "xlpe": ["xlpe", "cross-linked polyethylene"],
    "copper": ["copper", "cu"],
    "aluminium": ["aluminium", "aluminum", "al"],
    "steel": ["steel", "galvanized iron", "gi"],
    "rubber": ["rubber", "elastomer"]
}

APPLICATION_DOMAINS = {
    "power_distribution": ["power distribution", "distribution", "transmission", "substation", "grid"],
    "building_construction": ["building", "construction", "residential", "commercial", "housing"],
    "industrial": ["industrial", "factory", "plant", "manufacturing"],
    "water_supply": ["water supply", "plumbing", "drainage", "sewage"]
}

class FeatureService:
    def __init__(self, preprocessing_service: PreprocessingService = None):
        self.preprocessing_service = preprocessing_service or PreprocessingService()

    def extract_features(self, query: str) -> Dict[str, Any]:
        preprocessed = self.preprocessing_service.preprocess(query)
        normalized = preprocessed["normalized_query"]
        terms = preprocessed["terms"]
        units = preprocessed["units"]

        detected_products = []
        for cat, keywords in PRODUCT_CATEGORIES.items():
            if any(kw in normalized for kw in keywords):
                detected_products.append(cat)

        detected_materials = []
        for mat, keywords in MATERIAL_TYPES.items():
            if any(kw in normalized for kw in keywords):
                detected_materials.append(mat)

        detected_applications = []
        for app, keywords in APPLICATION_DOMAINS.items():
            if any(kw in normalized for kw in keywords):
                detected_applications.append(app)

        features = {
            "products": detected_products,
            "materials": detected_materials,
            "applications": detected_applications,
            "units": units,
            "keywords": terms,
            "normalized_query": normalized
        }
        return features
