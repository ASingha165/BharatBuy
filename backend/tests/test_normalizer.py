from backend.app.utils.text_normalizer import TextNormalizer

def test_normalize_is_codes():
    raw = "procurement of is694 cables and IS-1554"
    normalized = TextNormalizer.normalize_query(raw)
    assert "IS 694" in normalized
    assert "IS 1554" in normalized

def test_normalize_voltage_ratings():
    raw = "electrical cables for 1.1kV distribution"
    normalized = TextNormalizer.normalize_query(raw)
    assert "1.1 kV" in normalized
    assert "1100 V" in normalized

def test_tokenize():
    raw = "High yield strength deformed steel IS 1786"
    tokens = TextNormalizer.tokenize(raw)
    assert "high" in tokens
    assert "steel" in tokens
    assert "1786" in tokens
