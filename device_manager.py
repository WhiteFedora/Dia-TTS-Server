# device_manager.py
# Smart device detection and management for GPU (Colab T4) and CPU (local)

import logging
import os
import sys
import torch
import psutil
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Information about the compute device."""
    device_type: str  # 'cuda', 'mps', 'cpu'
    device_name: str  # GPU model or 'CPU'
    is_colab: bool
    compute_capability: Optional[Tuple[int, int]] = None
    total_memory_mb: Optional[float] = None
    available_memory_mb: Optional[float] = None
    cpu_count: int = 1
    is_low_memory: bool = False


def detect_environment() -> Dict[str, bool]:
    """
    Detect the runtime environment.
    
    Returns:
        Dict with keys 'is_colab', 'is_kaggle', 'is_docker', 'is_windows', 'is_linux', 'is_macos'
    """
    try:
        import google.colab
        is_colab = True
    except ImportError:
        is_colab = False

    is_kaggle = os.path.exists('/kaggle/input')
    is_docker = os.path.exists('/.dockerenv')
    is_windows = sys.platform == 'win32'
    is_linux = sys.platform == 'linux'
    is_macos = sys.platform == 'darwin'

    return {
        'is_colab': is_colab,
        'is_kaggle': is_kaggle,
        'is_docker': is_docker,
        'is_windows': is_windows,
        'is_linux': is_linux,
        'is_macos': is_macos
    }


def get_device_info(prefer_gpu: bool = True) -> DeviceInfo:
    """
    Intelligently detect and return device information.
    
    Args:
        prefer_gpu: If True, prefer GPU when available (for Colab). If False, use CPU only.
    
    Returns:
        DeviceInfo object with device details.
    """
    env = detect_environment()
    is_colab = env['is_colab']
    
    device_info = DeviceInfo(
        device_type='cpu',
        device_name='CPU',
        is_colab=is_colab,
        cpu_count=psutil.cpu_count(logical=False) or 1
    )
    
    # Get system memory info
    try:
        mem = psutil.virtual_memory()
        device_info.total_memory_mb = mem.total / (1024 ** 2)
        device_info.available_memory_mb = mem.available / (1024 ** 2)
        device_info.is_low_memory = device_info.available_memory_mb < 2048  # Less than 2GB
        logger.info(f"System memory: {device_info.available_memory_mb:.1f}MB available / {device_info.total_memory_mb:.1f}MB total")
    except Exception as e:
        logger.warning(f"Could not read system memory: {e}")
    
    # Check for GPU if prefer_gpu is True
    if prefer_gpu:
        if torch.cuda.is_available():
            device_info.device_type = 'cuda'
            device_info.device_name = torch.cuda.get_device_name(0)
            
            # Get CUDA info
            try:
                device_info.compute_capability = torch.cuda.get_device_capability(0)
                props = torch.cuda.get_device_properties(0)
                device_info.total_memory_mb = props.total_memory / (1024 ** 2)
                device_info.available_memory_mb = (props.total_memory - torch.cuda.memory_allocated()) / (1024 ** 2)
                logger.info(f"CUDA device detected: {device_info.device_name}")
                logger.info(f"Compute capability: {device_info.compute_capability}")
                logger.info(f"GPU memory: {device_info.available_memory_mb:.1f}MB available / {device_info.total_memory_mb:.1f}MB total")
            except Exception as e:
                logger.warning(f"Could not read CUDA memory: {e}")
                
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device_info.device_type = 'mps'
            device_info.device_name = 'Apple Metal Performance Shaders'
            logger.info("MPS device detected (Apple Silicon)")
    
    return device_info


def get_optimal_dtype(device_info: DeviceInfo, weights_filename: str = "") -> str:
    """
    Determine optimal compute dtype based on device capabilities.
    
    Args:
        device_info: DeviceInfo object with device details.
        weights_filename: Optional filename to detect model precision (e.g., 'dia-v0_1_bf16.safetensors').
    
    Returns:
        String representing dtype: 'float32', 'float16', 'bfloat16'.
    """
    is_bf16_model = 'bf16' in weights_filename.lower()
    
    if device_info.device_type == 'cuda':
        compute_capability = device_info.compute_capability or (7, 0)
        supports_bf16 = torch.cuda.is_bf16_supported()
        supports_fp16 = compute_capability[0] >= 7  # Turing and newer
        
        if is_bf16_model:
            if supports_bf16:
                logger.info("BF16 model + BF16 supported → using bfloat16")
                return 'bfloat16'
            elif supports_fp16:
                logger.warning("BF16 model but BF16 not supported → falling back to float16")
                return 'float16'
            else:
                logger.warning("BF16 model but neither BF16 nor efficient FP16 supported → using float32")
                return 'float32'
        else:
            logger.info("Non-BF16 model on CUDA → using float32 for compatibility")
            return 'float32'
    
    elif device_info.device_type == 'mps':
        logger.info("MPS device → using float16")
        return 'float16'
    
    else:  # CPU
        logger.info("CPU device → using float32")
        return 'float32'


def get_optimal_device(prefer_gpu: bool = True) -> torch.device:
    """
    Get optimal device with intelligent selection.
    
    Args:
        prefer_gpu: Prefer GPU when available.
    
    Returns:
        torch.device object.
    """
    device_info = get_device_info(prefer_gpu=prefer_gpu)
    logger.info(f"Selected device: {device_info.device_type.upper()} ({device_info.device_name})")
    return torch.device(device_info.device_type)


def log_device_info(device_info: DeviceInfo) -> None:
    """Log detailed device information."""
    logger.info(f"=== Device Information ===")
    logger.info(f"Device Type: {device_info.device_type.upper()}")
    logger.info(f"Device Name: {device_info.device_name}")
    logger.info(f"Colab Environment: {device_info.is_colab}")
    if device_info.compute_capability:
        logger.info(f"Compute Capability: {device_info.compute_capability}")
    if device_info.total_memory_mb:
        logger.info(f"Total Memory: {device_info.total_memory_mb:.1f} MB")
    if device_info.available_memory_mb:
        logger.info(f"Available Memory: {device_info.available_memory_mb:.1f} MB")
    logger.info(f"CPU Cores: {device_info.cpu_count}")
    logger.info(f"Low Memory Mode: {device_info.is_low_memory}")
    logger.info(f"========================")
