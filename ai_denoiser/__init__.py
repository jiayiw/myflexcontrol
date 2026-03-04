"""AI Audio Denoiser Module

Provides GPU-accelerated or CPU-friendly audio denoising for FlexRadio 6400.
Supports SpeechBrain (GPU) and DeepFilterNet (CPU) engines.
"""

from .detector import detect_gpu
from .model_manager import get_denoiser, needs_download
from .interface import BaseDenoiser

__all__ = ["detect_gpu", "get_denoiser", "needs_download", "BaseDenoiser"]
