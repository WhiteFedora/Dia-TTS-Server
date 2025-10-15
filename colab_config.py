# colab_config.py
# Configuration management for Dia TTS in Google Colab

import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ColabConfig:
    """Configuration settings for Colab TTS environment."""

    # Model settings
    model_repo_id: str = "ttj/dia-1.6b-safetensors"
    model_config_filename: str = "config.json"
    model_weights_filename: str = "dia-v0_1_bf16.safetensors"
    whisper_model_name: str = "small.en"

    # Path settings (Colab-specific)
    base_path: str = "/content/dia_tts"
    model_cache_path: str = "/content/dia_tts/models"
    reference_audio_path: str = "/content/dia_tts/reference_audio"
    voices_path: str = "/content/dia_tts/voices"
    outputs_path: str = "/content/dia_tts/outputs"

    # Generation defaults
    speed_factor: float = 1.0
    cfg_scale: float = 3.0
    temperature: float = 1.3
    top_p: float = 0.95
    cfg_filter_top_k: int = 35
    seed: int = 42
    split_text: bool = True
    chunk_size: int = 120

    # UI state
    last_text: str = "[S1] Hello! This is a test of the Dia TTS system running in Google Colab."
    last_voice_mode: str = "dialogue"
    last_predefined_voice: Optional[str] = None
    last_reference_file: Optional[str] = None
    last_split_text_enabled: bool = True

    # Hardware settings
    use_gpu: bool = True
    device: str = "auto"  # "auto", "cpu", "cuda"


class ColabConfigManager:
    """Manages configuration for Colab TTS environment."""

    def __init__(self):
        self.config = ColabConfig()
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories in Colab environment."""
        directories = [
            self.config.model_cache_path,
            self.config.reference_audio_path,
            self.config.voices_path,
            self.config.outputs_path,
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def get_config(self) -> ColabConfig:
        """Get current configuration."""
        return self.config

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"Warning: Unknown configuration key '{key}'")

    def save_config(self, filepath: str = "/content/dia_tts/config.json"):
        """Save configuration to JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)

    def load_config(self, filepath: str = "/content/dia_tts/config.json"):
        """Load configuration from JSON file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

    def get_device(self) -> str:
        """Determine the best available device."""
        import torch

        if not self.config.use_gpu:
            return "cpu"

        if self.config.device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        else:
            return self.config.device

    def get_compute_dtype(self) -> str:
        """Determine compute dtype based on device and model."""
        import torch

        device = self.get_device()
        weights_filename = self.config.model_weights_filename
        is_bf16_model = "bf16" in weights_filename.lower()

        if device == "cuda":
            if is_bf16_model and torch.cuda.is_bf16_supported():
                return "bfloat16"
            elif torch.cuda.get_device_capability()[0] >= 7:
                return "float16"
            else:
                return "float32"
        elif device == "mps":
            return "float16"
        else:  # CPU
            return "float32"


# Global config manager instance
config_manager = ColabConfigManager()


def get_config() -> ColabConfig:
    """Get the global configuration instance."""
    return config_manager.get_config()


def update_config(updates: Dict[str, Any]):
    """Update the global configuration."""
    config_manager.update_config(updates)


def get_device() -> str:
    """Get the current device setting."""
    return config_manager.get_device()


def get_compute_dtype() -> str:
    """Get the current compute dtype setting."""
    return config_manager.get_compute_dtype()


# Convenience getters for commonly used paths
def get_model_cache_path() -> str:
    return config_manager.config.model_cache_path


def get_reference_audio_path() -> str:
    return config_manager.config.reference_audio_path


def get_voices_path() -> str:
    return config_manager.config.voices_path


def get_outputs_path() -> str:
    return config_manager.config.outputs_path


def get_model_repo_id() -> str:
    return config_manager.config.model_repo_id


def get_model_config_filename() -> str:
    return config_manager.config.model_config_filename


def get_model_weights_filename() -> str:
    return config_manager.config.model_weights_filename


def get_whisper_model_name() -> str:
    return config_manager.config.whisper_model_name


# Generation parameter getters
def get_gen_default_speed_factor() -> float:
    return config_manager.config.speed_factor


def get_gen_default_cfg_scale() -> float:
    return config_manager.config.cfg_scale


def get_gen_default_temperature() -> float:
    return config_manager.config.temperature


def get_gen_default_top_p() -> float:
    return config_manager.config.top_p


def get_gen_default_cfg_filter_top_k() -> int:
    return config_manager.config.cfg_filter_top_k


def get_gen_default_seed() -> int:
    return config_manager.config.seed


def get_gen_default_split_text() -> bool:
    return config_manager.config.split_text


def get_gen_default_chunk_size() -> int:
    return config_manager.config.chunk_size
