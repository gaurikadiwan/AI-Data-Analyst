"""
LLM Service
Handles Ollama model loading. One model per request — no auto-fallback.
"""

from langchain_ollama import ChatOllama
from config.config import Config


# ============================================================
# Default Model
# ============================================================

DEFAULT_MODEL = "tinyllama"
CURRENT_MODEL = DEFAULT_MODEL


# ============================================================
# Per-model cache (singleton per model name)
# ============================================================

_llm_instances: dict[str, ChatOllama] = {}


# ============================================================
# Model Configurations
# ============================================================

MODEL_CONFIGS = {

    "tinyllama": {
        "temperature": 0.3,
        "num_predict": 180,
        "top_k": 20,
        "top_p": 0.8,
        "repeat_penalty": 1.1,
    },

    "phi3:mini": {
        "temperature": 0.4,
        "num_predict": 250,
        "top_k": 40,
        "top_p": 0.9,
        "repeat_penalty": 1.05,
    },

    "qwen2.5-coder:3b": {
        "temperature": 0.2,
        "num_predict": 220,
        "top_k": 30,
        "top_p": 0.85,
        "repeat_penalty": 1.1,
    }
}


# ============================================================
# Get LLM — one model per call, no fallback
# ============================================================

def get_llm(model=None):
    """
    Return a cached ChatOllama instance for the given model.
    Defaults to tinyllama if no model is specified.
    """

    model_name = model or DEFAULT_MODEL

    if model_name not in _llm_instances:
        config = MODEL_CONFIGS.get(
            model_name,
            MODEL_CONFIGS["tinyllama"]
        )
        _llm_instances[model_name] = ChatOllama(
            model=model_name,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=config["temperature"],
            num_predict=config["num_predict"],
            top_k=config["top_k"],
            top_p=config["top_p"],
            repeat_penalty=config["repeat_penalty"],
        )

    return _llm_instances[model_name]


# ============================================================
# Model Metadata
# ============================================================

def get_llm_for_model(model_name):
    """
    Create a temporary LLM instance for a specific model
    without affecting the cache.
    """
    config = MODEL_CONFIGS.get(
        model_name,
        MODEL_CONFIGS["tinyllama"]
    )
    return ChatOllama(
        model=model_name,
        base_url=Config.OLLAMA_BASE_URL,
        temperature=config["temperature"],
        num_predict=config["num_predict"],
        top_k=config["top_k"],
        top_p=config["top_p"],
        repeat_penalty=config["repeat_penalty"],
    )


def set_model(model_name):
    global CURRENT_MODEL
    if model_name not in MODEL_CONFIGS and model_name != DEFAULT_MODEL:
        raise ValueError(f"Unknown model: {model_name}")
    CURRENT_MODEL = model_name
    return get_model_info()


def get_model_info():
    """
    Return model metadata.
    """

    available_models = [
        "tinyllama",
        "phi3:mini",
        "qwen2.5-coder:3b"
    ]

    return {

        "model": CURRENT_MODEL,

        "lightweight": CURRENT_MODEL in [
            "tinyllama",
            "phi3:mini"
        ],

        "available_models": available_models
    }