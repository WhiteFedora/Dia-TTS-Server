# memory_optimizer.py
# Memory optimization utilities for CPU and GPU environments

import logging
import torch
import gc
import psutil
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Configuration for memory optimization."""
    enable_gradient_checkpointing: bool = True
    enable_activation_checkpointing: bool = True
    enable_cpu_offloading: bool = False
    use_mixed_precision: bool = False
    quantization_method: Optional[str] = None  # 'int8', 'int4', None
    max_memory_allocation_mb: Optional[float] = None
    enable_memory_profiling: bool = False


class MemoryOptimizer:
    """Manages memory optimization for different device types."""
    
    def __init__(self, device_type: str, device_info: Optional[dict] = None):
        """
        Initialize memory optimizer.
        
        Args:
            device_type: 'cuda', 'mps', or 'cpu'.
            device_info: Optional dict with device capabilities.
        """
        self.device_type = device_type
        self.device_info = device_info or {}
        self.is_low_memory = device_info.get('is_low_memory', False) if device_info else False
        
    def get_recommended_config(self) -> MemoryConfig:
        """
        Get recommended memory configuration based on device type.
        
        Returns:
            MemoryConfig with recommended settings.
        """
        if self.device_type == 'cuda':
            # GPU (Colab T4) - can afford more aggressive optimizations
            return MemoryConfig(
                enable_gradient_checkpointing=False,  # Training not needed
                enable_activation_checkpointing=False,
                enable_cpu_offloading=False,
                use_mixed_precision=True,
                quantization_method=None,
                enable_memory_profiling=True
            )
        
        elif self.is_low_memory or self.device_type == 'cpu':
            # Low-memory CPU environment
            return MemoryConfig(
                enable_gradient_checkpointing=False,
                enable_activation_checkpointing=False,
                enable_cpu_offloading=True,
                use_mixed_precision=False,
                quantization_method='int8',  # Quantize model weights
                max_memory_allocation_mb=4096,  # Limit memory usage
                enable_memory_profiling=True
            )
        
        else:  # MPS or unknown
            return MemoryConfig(
                enable_gradient_checkpointing=False,
                enable_activation_checkpointing=False,
                enable_cpu_offloading=False,
                use_mixed_precision=True,
                quantization_method=None,
                enable_memory_profiling=True
            )
    
    def cleanup_memory(self, clear_gpu_cache: bool = True, clear_cpu_cache: bool = True) -> None:
        """
        Perform aggressive memory cleanup.
        
        Args:
            clear_gpu_cache: Clear GPU cache if device is CUDA.
            clear_cpu_cache: Clear CPU memory via garbage collection.
        """
        if clear_cpu_cache:
            gc.collect()
            logger.debug("CPU memory garbage collection completed")
        
        if clear_gpu_cache and self.device_type == 'cuda':
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.debug("GPU cache cleared")
    
    def get_memory_usage_mb(self) -> dict:
        """
        Get current memory usage.
        
        Returns:
            Dict with 'cpu_mb', 'gpu_mb' (if applicable), and 'total_mb'.
        """
        usage = {}
        
        # CPU memory
        try:
            process = psutil.Process()
            usage['cpu_mb'] = process.memory_info().rss / (1024 ** 2)
        except Exception as e:
            logger.warning(f"Could not read CPU memory: {e}")
            usage['cpu_mb'] = 0
        
        # GPU memory
        if self.device_type == 'cuda':
            try:
                usage['gpu_mb'] = torch.cuda.memory_allocated() / (1024 ** 2)
            except Exception as e:
                logger.warning(f"Could not read GPU memory: {e}")
                usage['gpu_mb'] = 0
        
        usage['total_mb'] = sum(v for v in usage.values())
        return usage
    
    def log_memory_status(self, prefix: str = "Memory Status") -> None:
        """Log current memory usage."""
        usage = self.get_memory_usage_mb()
        logger.info(f"{prefix}: CPU={usage.get('cpu_mb', 0):.1f}MB, GPU={usage.get('gpu_mb', 0):.1f}MB, Total={usage['total_mb']:.1f}MB")


def estimate_model_memory_mb(num_params: int, dtype: str = 'float32', include_activations: bool = True) -> float:
    """
    Estimate model memory usage.
    
    Args:
        num_params: Number of model parameters.
        dtype: Data type ('float32', 'float16', 'bfloat16', 'int8').
        include_activations: Include activation memory estimate (roughly 2x parameters).
    
    Returns:
        Estimated memory in MB.
    """
    dtype_to_bytes = {
        'float32': 4,
        'float': 4,
        'float16': 2,
        'half': 2,
        'bfloat16': 2,
        'int8': 1,
    }
    
    bytes_per_param = dtype_to_bytes.get(dtype, 4)
    model_mb = (num_params * bytes_per_param) / (1024 ** 2)
    
    if include_activations:
        model_mb *= 3  # Rough estimate: weights + activations + gradients (if training)
    
    return model_mb
