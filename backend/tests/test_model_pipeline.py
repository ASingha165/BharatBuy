import pytest
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.services.feature_service import FeatureService
from backend.app.services.baseline_model import BaselineRecommendationModel
from backend.app.services.custom_model import CustomTrainedModel

def test_preprocessing_service():
    prep = PreprocessingService()
    res = prep.preprocess("Procurement of 1.1 kV PVC insulated power cables for 50 Hz grid")
    assert res["normalized_query"] == "procurement of 1.1 kv pvc insulated power cables for 50 hz grid"
    assert "1.1 kv" in res["units"]["voltage"]
    assert "cables" in res["terms"]

def test_feature_service():
    fs = FeatureService()
    features = fs.extract_features("Procurement of 1.1 kV PVC insulated power distribution cables")
    assert "cable" in features["products"]
    assert "pvc" in features["materials"]
    assert "power_distribution" in features["applications"]

def test_baseline_recommendation_model():
    model = BaselineRecommendationModel()
    candidates = [
        {
            "standard_id": "IS-694",
            "is_code": "IS 694",
            "title": "PVC Insulated Cables for Working Voltages Up to and Including 1100 V",
            "department": "Electro-technical",
            "scope_summary": "Polyvinyl Chloride Insulated Cables for Working Voltages Up to 1100V",
            "key_specifications": "Voltage rating 1.1 kV",
            "testing_requirements": "High voltage test"
        },
        {
            "standard_id": "IS-456",
            "is_code": "IS 456",
            "title": "Plain and Reinforced Concrete - Code of Practice",
            "department": "Civil Engineering",
            "scope_summary": "Structural concrete design",
            "key_specifications": "Compressive strength",
            "testing_requirements": "Slump test"
        }
    ]
    fs = FeatureService()
    features = fs.extract_features("1.1 kV PVC power cable")
    results = model.predict("1.1 kV PVC power cable", features, candidates, top_k=5)
    
    assert len(results) == 2
    top_std, score, reason = results[0]
    assert top_std["standard_id"] == "IS-694"
    assert score > 0.5
    assert "1.1 kV" in reason or "cable" in reason.lower()

def test_custom_model_fallback():
    custom_model = CustomTrainedModel()
    candidates = [
        {
            "standard_id": "IS-694",
            "is_code": "IS 694",
            "title": "PVC Insulated Cables",
            "department": "Electro-technical"
        }
    ]
    fs = FeatureService()
    features = fs.extract_features("cables")
    results = custom_model.predict("cables", features, candidates, top_k=5)
    assert len(results) == 1
    assert results[0][0]["standard_id"] == "IS-694"
