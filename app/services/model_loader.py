import os
import joblib

_models = {}
MODELS_DIR = "models"


def load_models():
    global _models
    if not os.path.exists(MODELS_DIR):
        print(f"  [XƏTA] '{MODELS_DIR}' qovluğu tapılmadı.")
        return

    for fname in os.listdir(MODELS_DIR):
        if fname.endswith(".joblib"):
            model_name = fname.replace(".joblib", "")
            path = os.path.join(MODELS_DIR, fname)

            try:
                _models[model_name] = joblib.load(path)
                print(f"  Loaded model: {model_name}")
            except Exception as e:
                print(f"  [XƏTA] {fname} yüklənərkən xəta baş verdi: {e}")

    if not _models:
        print("  No models found — running in stub mode")


def get_model(name: str):
    return _models.get(name)


def get_all_models():
    return _models