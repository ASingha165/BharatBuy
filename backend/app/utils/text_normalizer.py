import re

class TextNormalizer:
    @staticmethod
    def normalize_query(query: str) -> str:
        if not query:
            return ""
            
        # Convert to lowercase for uniform processing, but preserve numbers and standard patterns
        text = query.strip()
        
        # Standardize IS code variations: "is694" -> "IS 694", "is 694" -> "IS 694", "is-694" -> "IS 694"
        text = re.sub(r'\b(?:is|IS)[-_\s]*(\d+)(?:[-_\s]*(part|pt|\()?[-_\s]*(\d+)\)?)?\b', r'IS \1 \2 \3', text, flags=re.IGNORECASE)
        
        # Standardize voltage ratings: "1.1kv", "1.1 kv", "1100v", "1100 v"
        text = re.sub(r'\b1\.?1\s*k[vV]\b', '1.1 kV 1100 V', text)
        text = re.sub(r'\b1100\s*[vV]\b', '1100 V 1.1 kV', text)
        text = re.sub(r'\b3\.?3\s*k[vV]\b', '3.3 kV', text)
        text = re.sub(r'\b11\s*k[vV]\b', '11 kV', text)
        text = re.sub(r'\b33\s*k[vV]\b', '33 kV', text)
        
        # Clean extra punctuation but preserve decimals and hyphens in technical codes
        text = re.sub(r'[^\w\s\.-]', ' ', text)
        
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    @staticmethod
    def tokenize(text: str) -> list[str]:
        cleaned = TextNormalizer.normalize_query(text).lower()
        tokens = [t for t in re.split(r'\W+', cleaned) if len(t) > 1]
        return tokens
