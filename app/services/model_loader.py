import os
import joblib

_models = {}

MODELS_DIR = "models"


def load_models():
    global _models

    forecast_dir = os.path.join(MODELS_DIR, "forecast")
    if os.path.exists(forecast_dir):
        for fname in os.listdir(forecast_dir):
            if fname.endswith(".joblib"):
                region = fname.replace(".joblib", "")
                path = os.path.join(forecast_dir, fname)
                _models[f"forecast_{region}"] = joblib.load(path)
                print(f"  Loaded forecast model: {region}")

    avg_weight_path = os.path.join(MODELS_DIR, "avg_weight_model.joblib")
    if os.path.exists(avg_weight_path):
        _models["avg_weight"] = joblib.load(avg_weight_path)
        print("  Loaded avg_weight model")

    if not _models:
        print("  No models found — running in stub mode")


def get_model(name: str):
    return _models.get(name)


def get_all_models():
    return _models