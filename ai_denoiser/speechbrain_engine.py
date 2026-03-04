"""SpeechBrain SepFormer engine for GPU-accelerated denoising

This module provides GPU-accelerated speech enhancement using SpeechBrain's
SepFormer model. Requires CUDA-capable GPU with at least 8GB VRAM.

Model: speechbrain/sepformer-librispeech-voxconverse
Size: ~400MB
Latency: ~100ms
Requirements: torch >= 2.0.0, speechbrain >= 1.0.0
"""

import os
import torch
import torch.nn.functional as F
import numpy as np
from typing import Optional
from .interface import BaseDenoiser


class SpeechBrainDenoiser(BaseDenoiser):
    """SpeechBrain SepFormer for speech enhancement

    Attributes:
        cache_dir: Directory for model cache
        use_cuda: Whether to use GPU acceleration
        model: Pretrained SepFormer model
        ready: Whether model is loaded and ready
    """

    MODEL_ID = "speechbrain/sepformer-librispeech-voxconverse"
    SAMPLE_RATE = 48000
    CHUNK_SAMPLES = 4800  # 100ms at 48kHz

    def __init__(self, cache_dir: str, use_cuda: bool = True):
        """Initialize SpeechBrain denoiser

        Args:
            cache_dir: Directory to cache model files
            use_cuda: Whether to use CUDA (should be True if GPU available)
        """
        self.cache_dir = cache_dir
        self.use_cuda = use_cuda
        self.device = torch.device(
            "cuda" if use_cuda and torch.cuda.is_available() else "cpu"
        )
        self.model = None
        self.ready = False

    def load_model(self) -> bool:
        """Load model from cache or download

        Returns:
            True if model loaded successfully
        """
        try:
            from speechbrain.inference import SEPR
            from huggingface_hub import snapshot_download
            import shutil

            # Ensure cache directory exists
            local_name = self.MODEL_ID.replace("/", "_")
            local_dir = os.path.join(self.cache_dir, local_name)
            os.makedirs(local_dir, exist_ok=True)

            # Check if already downloaded
            if not os.path.exists(os.path.join(local_dir, "pretrained.yaml")):
                print(f"Downloading model to {local_dir}...")
                try:
                    snapshot_download(
                        repo_id=self.MODEL_ID,
                        allow_patterns=["*.yaml", "*.pt", "*.json"],
                        cache_dir=local_dir,
                        local_dir=local_dir,
                    )
                except Exception as e:
                    print(f"HuggingFace download failed: {e}")
                    print("Trying SpeechBrain native download...")

            # Load pretrained model via SpeechBrain
            self.model = SEPR.from_hparams(
                source=self.MODEL_ID,
                savedir=local_dir,
                run_args={"device": str(self.device)},
            )

            self.model.eval()
            self.model.to(self.device)
            self.ready = True

            print(f"SpeechBrain model loaded on {self.device}")
            return True

        except Exception as e:
            print(f"Failed to load SpeechBrain model: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _convert_audio(self, audio_data: bytes) -> Optional[torch.Tensor]:
        """Convert bytes to waveform tensor

        Args:
            audio_data: Raw 16-bit PCM audio (48kHz, mono)

        Returns:
            Waveform tensor normalized to [-1, 1]
        """
        try:
            if len(audio_data) % 2 != 0:
                audio_data = audio_data[:-1]

            samples = (
                np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            )
            return torch.tensor(samples).unsqueeze(0).to(self.device)
        except Exception as e:
            print(f"Failed to convert audio: {e}")
            return None

    def _convert_back(self, waveform: torch.Tensor) -> bytes:
        """Convert waveform tensor back to bytes

        Args:
            waveform: Waveform tensor in range [-1, 1]

        Returns:
            Raw 16-bit PCM bytes
        """
        try:
            cpu_np = waveform.squeeze().cpu().numpy()
            cpu_np = np.clip(cpu_np, -1, 1) * 32768
            return cpu_np.astype(np.int16).tobytes()
        except Exception as e:
            print(f"Failed to convert waveform: {e}")
            return b""

    def process(self, audio_data: bytes) -> Optional[bytes]:
        """Process audio data with denoising

        Args:
            audio_data: Raw 16-bit PCM audio data

        Returns:
            Denoised audio data, or None if processing failed
        """
        if not self.ready or not audio_data:
            return None

        try:
            # Convert to tensor
            waveform = self._convert_audio(audio_data)
            if waveform is None:
                return None

            # Ensure minimum length
            if waveform.shape[1] < self.CHUNK_SAMPLES:
                pad_len = self.CHUNK_SAMPLES - waveform.shape[1]
                waveform = F.pad(waveform, (0, pad_len))

            # Process with model
            with torch.no_grad():
                enhanced = self.model.enhance_batch(waveform)

            # Convert back to bytes
            return self._convert_back(enhanced)

        except Exception as e:
            print(f"Denoising failed: {e}")
            return None

    def is_ready(self) -> bool:
        """Check if denoiser is ready"""
        return self.ready

    def cleanup(self) -> None:
        """Release resources"""
        if self.model:
            del self.model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.model = None
            self.ready = False
            print("SpeechBrain model unloaded")
