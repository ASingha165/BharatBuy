import re
from typing import Dict, List, Any, Set

STOP_WORDS: Set[str] = {
    "a", "an", "the", "for", "and", "or", "in", "on", "at", "to", "with", "by", "of", "from",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
    "procurement", "supply", "purchase", "installation", "requirement", "specification", "specifications", "needed", "required"
}

class PreprocessingService:
    @staticmethod
    def normalize_text(text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s\.-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text

    @staticmethod
    def extract_units(text: str) -> Dict[str, List[str]]:
        units: Dict[str, List[str]] = {
            "voltage": [],
            "current": [],
            "power": [],
            "frequency": [],
            "dimensions": []
        }
        if not text:
            return units

        # Voltage pattern (e.g., 1.1 kv, 1100 v, 11kv, 415v, 33 kv)
        voltages = re.findall(r'\b(?:\d+(?:\.\d+)?)\s*(?:kv|kilo\s*volts?|v|volts?)\b', text, re.IGNORECASE)
        for v in voltages:
            cleaned = v.lower().strip()
            # Canonicalize 1.1 kv / 1100 v equivalency
            if "1.1" in cleaned and "kv" in cleaned:
                units["voltage"].extend(["1.1 kv", "1100 v", "1100v", "1.1kv"])
            else:
                units["voltage"].append(cleaned)

        # Current pattern (e.g., 500 a, 100 amps)
        currents = re.findall(r'\b(?:\d+(?:\.\d+)?)\s*(?:a|amps?|amperes?)\b', text, re.IGNORECASE)
        units["current"] = [c.lower().strip() for c in currents]

        # Power pattern (e.g., 100 kw, 1 mw, 50 hp)
        powers = re.findall(r'\b(?:\d+(?:\.\d+)?)\s*(?:kw|mw|hp|kva|mva)\b', text, re.IGNORECASE)
        units["power"] = [p.lower().strip() for p in powers]

        # Frequency pattern (e.g., 50 hz, 60 hz)
        frequencies = re.findall(r'\b(?:\d+)\s*(?:hz|hertz)\b', text, re.IGNORECASE)
        units["frequency"] = [f.lower().strip() for f in frequencies]

        # Dimensions / cross section (e.g., 2.5 sq mm, 4 mm2, 10 mm)
        dims = re.findall(r'\b(?:\d+(?:\.\d+)?)\s*(?:sq\s*mm|mm2|mm|cm|m)\b', text, re.IGNORECASE)
        units["dimensions"] = [d.lower().strip() for d in dims]

        return units

    @staticmethod
    def extract_technical_terms(text: str) -> List[str]:
        normalized = PreprocessingService.normalize_text(text)
        tokens = normalized.split()
        terms = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
        return terms

    def preprocess(self, query: str) -> Dict[str, Any]:
        normalized_query = self.normalize_text(query)
        units = self.extract_units(query)
        terms = self.extract_technical_terms(query)
        
        return {
            "raw_query": query,
            "normalized_query": normalized_query,
            "terms": terms,
            "units": units
        }
