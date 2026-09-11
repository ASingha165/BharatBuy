# Custom ML Model Training Guide (SIH26108)

This directory is dedicated to your team's custom machine-learning model development and training workflow.

---

## Workflow Overview

1. **Prepare Training Data**:
   - Collect procurement requirement queries paired with ground-truth relevant Indian Standard (IS) codes from historical procurement records or BIS catalog mappings.
   - Store training data under `data/training_dataset.csv` or `data/training_dataset.json`.

2. **Feature Extraction**:
   - Utilize `FeatureService` (`backend/app/services/feature_service.py`) and `PreprocessingService` (`backend/app/services/preprocessing_service.py`) to convert raw text into structured features (products, materials, voltages, capacities, keywords).

3. **Train Model**:
   - Train your custom model (e.g. Scikit-Learn `RandomForestClassifier`, `GradientBoostingClassifier`, PyTorch neural ranker, LightGBM, or ONNX model).

4. **Evaluate Model**:
   - Measure Mean Reciprocal Rank (MRR), Precision@K, and Normalized Discounted Cumulative Gain (NDCG@10) on a hold-out test set.

5. **Save Model Artifact**:
   - Save your serialized model artifact to `models/custom_recommendation_model.pkl`:
     ```python
     import pickle
     with open("models/custom_recommendation_model.pkl", "wb") as f:
         pickle.dump(trained_model, f)
     ```

6. **Activate Custom Model**:
   - Update `.env`:
     ```env
     MODEL_TYPE=custom
     CUSTOM_MODEL_PATH=models/custom_recommendation_model.pkl
     ```
   - Restart FastAPI backend. The system will automatically serve predictions via `CustomTrainedModel`.
