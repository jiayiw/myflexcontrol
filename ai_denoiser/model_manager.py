"""Model selection and management module

Handles automatic selection of appropriate denoiser engine based on:
- GPU availability and VRAM
- User configuration
- Fallback preferences
"""

import os
from typing import Optional
from .detector import detect_gpu
from .interface import BaseDenoiser


# Lazy imports to avoid dependency on startup
def _import_speechbrain_engine():
    """Import SpeechBrain engine only when needed"""
    from .speechbrain_engine import SpeechBrainDenoiser

    return SpeechBrainDenoiser


def _import_deepfilter_engine():
    """Import DeepFilterNet engine only when needed"""
    from .deepfilter_engine import DeepFilterDenoiser

    return DeepFilterDenoiser


def get_denoiser(config: dict) -> Optional[BaseDenoiser]:
    """Select and initialize appropriate denoiser based on config and GPU availability

    Args:
        config: AI denoiser configuration dictionary
                Keys:
                - enabled: bool
                - model_cache_dir: str
                - fallback_mode: str ("deepfilter" or "disable")
                - manual_fallback: bool

    Returns:
        Initialized denoiser instance or None if disabled/unavailable
    """
    if not config.get("enabled", False):
        return None

    cache_dir = config.get(
        "model_cache_dir", os.path.expanduser("~/.cache/flexradio/ai_models")
    )
    fallback_mode = config.get("fallback_mode", "deepfilter")
    manual_fallback = config.get("manual_fallback", False)

    # Detect GPU
    gpu_info = detect_gpu()

    # Try GPU mode first if available and sufficient VRAM
    if gpu_info.get("meets_requirement", False):
        print("Using GPU-accelerated SpeechBrain denoiser")
        SpeechBrainDenoiser = _import_speechbrain_engine()
        denoiser = SpeechBrainDenoiser(cache_dir, use_cuda=True)
        if denoiser.load_model():
            return denoiser
        print("SpeechBrain failed, falling back to CPU mode")

    # Fallback modes
    use_cpu_fallback = fallback_mode == "deepfilter" or manual_fallback

    if use_cpu_fallback:
        print("Using CPU-friendly DeepFilterNet denoiser")
        DeepFilterDenoiser = _import_deepfilter_engine()
        denoiser = DeepFilterDenoiser(cache_dir)
        if denoiser.load_model():
            return denoiser
        print("DeepFilterNet failed, denoising unavailable")

    return None


def needs_download(config: dict) -> dict:
    """Check if models need to be downloaded

    Args:
        config: AI denoiser configuration dictionary

    Returns:
        dict with download status:
        - speechbrain_needed: bool
        - deepfilter_needed: bool
        - message: str (user-friendly message)
    """
    if not config.get("enabled", False):
        return {
            "speechbrain_needed": False,
            "deepfilter_needed": False,
            "message": "Denoiser disabled",
        }

    cache_dir = config.get(
        "model_cache_dir", os.path.expanduser("~/.cache/flexradio/ai_models")
    )

    # Detect GPU
    gpu_info = detect_gpu()
    needs_sp = False
    needs_df = False

    if gpu_info.get("meets_requirement", False):
        # Check SpeechBrain
        local_name = "speechbrain_sepformer_librispeech_voxconverse"
        local_dir = os.path.join(cache_dir, local_name)
        needs_sp = not os.path.exists(local_dir) or not os.listdir(local_dir)

    # Check DeepFilterNet (always check for CPU fallback)
    df_dir = os.path.join(cache_dir, "deepfilter")
    needs_df = not os.path.exists(df_dir) or not os.listdir(df_dir)

    if needs_sp or needs_df:
        if gpu_info.get("meets_requirement"):
            msg = f"GPU mode available ({gpu_info['memory_gb']:.1f}GB VRAM). Model download required."
        else:
            msg = "Using CPU mode (DeepFilterNet). Model download required."
    else:
        msg = "Models already downloaded."

    return {
        "speechbrain_needed": needs_sp,
        "deepfilter_needed": needs_df,
        "message": msg,
        "gpu_available": gpu_info.get("meets_requirement", False),
        "cpu_fallback": not gpu_info.get("meets_requirement", True),
    }


def download_model(denoiser_type: str, cache_dir: str, callback=None) -> bool:
    """Download model file

    Args:
        denoiser_type: "speechbrain" or "deepfilter"
        cache_dir: Directory to download to
        callback: Optional progress callback function

    Returns:
        True if download successful
    """
    from huggingface_hub import snapshot_download
    import os

    try:
        if denoiser_type == "speechbrain":
            repo_id = "speechbrain/sepformer-librispeech-voxconverse"
            local_name = repo_id.replace("/", "_")
        else:  # deepfilter
            repo_id = "mf0e6/deepfilter"
            local_name = "deepfilter"

        local_dir = os.path.join(cache_dir, local_name)
        os.makedirs(local_dir, exist_ok=True)

        print(f"Downloading {denoiser_type} model to {local_dir}...")

        snapshot_download(
            repo_id=repo_id,
            cache_dir=cache_dir,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
        )

        print(f"{denoiser_type.capitalize()} model downloaded successfully")
        return True

    except Exception as e:
        print(f"Failed to download {denoiser_type} model: {e}")
        return False


def get_status_message(config: dict) -> str:
    """Get user-friendly status message for settings dialog

    Args:
        config: AI denoiser configuration dictionary

    Returns:
        User-friendly status message
    """
    gpu_info = detect_gpu()

    if not config.get("enabled", False):
        return "AI Denoiser is currently disabled"

    if gpu_info.get("meets_requirement", False):
        return f"✓ GPU Ready: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB)"

    if gpu_info.get("available", False):
        return f"⚠ Limited GPU: {gpu_info['name']} ({gpu_info['memory_gb']:.1f}GB, need ≥8GB)"

    return "No GPU detected, will use CPU mode (DeepFilterNet)"
