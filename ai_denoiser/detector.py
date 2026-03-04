"""GPU Detection Module

Detects available GPU and checks if it meets AI Denoiser requirements.
"""

import subprocess
from typing import Dict, Optional


def detect_gpu() -> Dict:
    """
    Detect available GPU and check if meets AI Denoiser requirements.

    Returns:
        dict with keys:
        - available: bool - GPU is detected
        - name: Optional[str] - GPU name
        - memory_gb: float - Total VRAM in GB
        - meets_requirement: bool - True if >= 8GB
    """
    result = {
        "available": False,
        "name": None,
        "memory_gb": 0.0,
        "meets_requirement": False,
    }

    # Method 1: nvidia-smi (preferred)
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total",
                "--format=csv,noheader,nounits",
            ],
            timeout=10,
        ).decode()

        for line in output.strip().split("\n"):
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[1] != "[N/A]":
                name = parts[0]
                memory_kb = float(parts[1])
                memory_gb = memory_kb / 1024

                result["available"] = True
                result["name"] = name
                result["memory_gb"] = memory_gb

                if memory_gb >= 8:
                    result["meets_requirement"] = True
                    break
    except Exception:
        pass

    # Method 2: PyTorch (fallback)
    if not result["available"]:
        try:
            import torch

            if torch.cuda.is_available():
                result["available"] = True
                for i in range(torch.cuda.device_count()):
                    name = torch.cuda.get_device_name(i)
                    memory_gb = (
                        torch.cuda.get_device_properties(i).total_memory / 1024**3
                    )

                    result["name"] = name
                    result["memory_gb"] = memory_gb

                    if memory_gb >= 8:
                        result["meets_requirement"] = True
                        break
        except Exception:
            pass

    return result
