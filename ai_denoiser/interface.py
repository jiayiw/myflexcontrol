"""Base interface for AI audio denoiser

Defines the abstract base class that all denoiser engines must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseDenoiser(ABC):
    """Abstract base class for audio denoisers"""

    @abstractmethod
    def process(self, audio_data: bytes) -> Optional[bytes]:
        """Process audio data with denoising

        Args:
            audio_data: Raw 16-bit PCM audio data

        Returns:
            Denoised audio data, or None to pass original
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if denoiser is initialized and ready"""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources"""
        pass

    def is_empty(self, audio_data: bytes) -> bool:
        """Check if audio data is empty or silent

        Args:
            audio_data: Raw audio data to check

        Returns:
            True if audio is empty or silent
        """
        if not audio_data:
            return True

        try:
            import struct
            import math

            samples = struct.unpack(f"{len(audio_data) // 2}h", audio_data)
            if len(samples) < 10:
                return False

            rms = math.sqrt(sum(s * s for s in samples) / len(samples))
            return rms < 10  # Threshold for silence
        except Exception:
            return False
