# Quick Reference: Implementation Checklist

## 📋 Phase 1: Device & Memory Integration (IMMEDIATE - Days 1-2)

### Task 1.1: Integrate device_manager into engine.py
**File**: `engine.py`  
**Current Code** (Line ~120-127):
```python
def get_device() -> torch.device:
    logger.info("Forcing CPU device selection (CPU-only target environment).")
    return torch.device("cpu")
```

**Action**: Replace with:
```python
from device_manager import get_device_info, get_optimal_device, get_optimal_dtype, log_device_info

def get_device(prefer_gpu: bool = True) -> torch.device:
    """Get optimal device with intelligent selection."""
    device_info = get_device_info(prefer_gpu=prefer_gpu)
    log_device_info(device_info)
    return get_optimal_device(prefer_gpu=prefer_gpu)

def get_compute_dtype(device: torch.device, weights_filename: str) -> str:
    """Get optimal dtype based on device capabilities."""
    device_info = get_device_info(prefer_gpu=device.type=='cuda')
    return get_optimal_dtype(device_info, weights_filename)
```

**Testing**:
```bash
# On Colab: Should detect CUDA and use T4 GPU
# On local CPU: Should detect CPU and use float32
```

---

### Task 1.2: Integrate memory_optimizer into engine.py
**File**: `engine.py`  
**Add at module level** (after imports):
```python
from memory_optimizer import MemoryOptimizer

# Global memory optimizer
memory_optimizer = None

def initialize_memory_optimizer(device_type: str) -> None:
    """Initialize memory optimizer based on device type."""
    global memory_optimizer
    memory_optimizer = MemoryOptimizer(device_type)
    config = memory_optimizer.get_recommended_config()
    
    logger.info(f"Memory optimization enabled")
    logger.info(f"  Quantization: {config.quantization_method}")
    logger.info(f"  CPU offloading: {config.enable_cpu_offloading}")
    logger.info(f"  Mixed precision: {config.use_mixed_precision}")
```

**Update load_model()** function:
```python
def load_model():
    global dia_model, model_config_instance, model_device, MODEL_LOADED, EXPECTED_SAMPLE_RATE, memory_optimizer
    
    # ... existing code ...
    
    model_device = get_device()  # Now uses smart detection
    initialize_memory_optimizer(model_device.type)
    
    # ... rest of load_model ...
```

**Update generate_speech()** function:
```python
def generate_speech(...) -> Optional[Tuple[np.ndarray, int]]:
    # ... existing code ...
    
    # Before generation
    monitor.record("Request received")
    
    # After generation
    if memory_optimizer:
        memory_optimizer.cleanup_memory()
        memory_optimizer.log_memory_status("Post-generation")
    
    return final_audio_np, EXPECTED_SAMPLE_RATE
```

**Testing**:
```bash
# Verify memory stats logged at startup and after each generation
# On Colab: Should show GPU memory
# On local: Should show CPU memory and quantization config
```

---

### Task 1.3: Add config option for prefer_gpu
**File**: `config.py`  
**Add to default config**:
```python
DEVICE_CONFIG = {
    'prefer_gpu': True,      # Set to False for CPU-only testing
    'force_cpu': False,      # Override to CPU only
    'auto_detect': True,     # Auto-detect environment
}
```

**Add getter function**:
```python
def get_prefer_gpu() -> bool:
    """Get preference for GPU usage."""
    return config_manager.get('device', {}).get('prefer_gpu', True)
```

**Update engine.py load_model()**:
```python
from config import get_prefer_gpu

def load_model():
    prefer_gpu = get_prefer_gpu()
    model_device = get_device(prefer_gpu=prefer_gpu)  # Use config preference
```

---

## 📋 Phase 2: API Enhancements (Days 3-4)

### Task 2.1: Update request models in models.py
**File**: `models.py`

Add new request models:
```python
from prosody_manager import Emotion, SpeakingStyle, ProsodyProfile

class ProsodyRequest(BaseModel):
    """Prosody parameters for a turn."""
    rate: float = 1.0
    pitch: float = 0.0
    energy: float = 1.0
    emotion: str = "neutral"      # or Emotion enum
    style: str = "normal"          # or SpeakingStyle enum
    pause_ms: int = 0

class SpeakerProfileRequest(BaseModel):
    """Speaker profile for dialogue."""
    speaker_id: str
    name: Optional[str] = None
    voice_filename: Optional[str] = None
    transcript: Optional[str] = None
    default_prosody: Optional[ProsodyRequest] = None

class TurnRequest(BaseModel):
    """A single turn in dialogue."""
    speaker_id: str
    text: str
    prosody: Optional[ProsodyRequest] = None
    pause_ms: int = 0

class CustomTTSRequest(BaseModel):
    # ... existing fields ...
    
    # New fields
    prosody: Optional[ProsodyRequest] = None
    speaker_profiles: Optional[List[SpeakerProfileRequest]] = None
    emotion_arc: Optional[List[str]] = None  # List of emotion names
    turns: Optional[List[TurnRequest]] = None
```

---

### Task 2.2: Create /v2/audio/speech endpoint
**File**: `server.py`

```python
@app.post(
    "/v2/audio/speech",
    response_class=StreamingResponse,
    tags=["TTS Generation"],
    summary="Generate speech with prosody & emotion (V2)",
)
async def tts_v2_endpoint(request: CustomTTSRequest):
    """
    Enhanced TTS endpoint with prosody, emotion, and multi-speaker support.
    
    Features:
    - Speaker profiles with default prosody
    - Per-turn prosody override
    - Emotion arcs for natural dialogue progression
    - Voice cloning with prosody
    """
    # Implementation similar to existing /tts endpoint
    # but using prosody_manager for formatting
    pass
```

---

## 📋 Phase 3: Error Handling (Days 5-6)

### Task 3.1: Create error hierarchy
**File**: `errors.py` (new)

```python
class DiaError(Exception):
    """Base exception for Dia TTS."""
    pass

class TransientError(DiaError):
    """Transient error (retry-able)."""
    def __init__(self, message: str, retry_count: int = 3):
        super().__init__(message)
        self.retry_count = retry_count

class PermanentError(DiaError):
    """Permanent error (not retry-able)."""
    pass

class ResourceError(DiaError):
    """Resource error (memory, disk space)."""
    pass

class CloningError(PermanentError):
    """Voice cloning failed."""
    pass
```

---

## 📋 Phase 4: Documentation & Tests (Days 7-9)

### Task 4.1: Create example scripts

**File**: `examples/simple_dialog.py`
```python
"""Simple multi-turn dialogue example."""
from prosody_manager import ProsodyManager, SpeakerProfile, ProsodyProfile, Emotion
from engine import generate_speech

manager = ProsodyManager()

# Register speakers
alice = SpeakerProfile(speaker_id='S1', name='Alice', voice_filename='alice.wav')
bob = SpeakerProfile(speaker_id='S2', name='Bob')
manager.register_speaker(alice)
manager.register_speaker(bob)

# Generate dialogue
dialogue = [
    ('S1', 'Hello Bob!', Emotion.HAPPY),
    ('S2', 'Hi Alice, how are you?', Emotion.NEUTRAL),
    ('S1', 'Great! I have exciting news!', Emotion.EXCITED),
]

for speaker, text, emotion in dialogue:
    prosody = ProsodyProfile(emotion=emotion)
    formatted_text = manager.build_turn_text(speaker, text, prosody)
    
    audio, sr = generate_speech(
        text_to_process=formatted_text,
        voice_mode='clone' if speaker == 'S1' else 'single_s2',
        clone_reference_filename='alice.wav' if speaker == 'S1' else None,
    )
    print(f"{speaker}: Generated {len(audio)} samples")
```

**File**: `examples/emotion_arc.py`
```python
"""Dialogue with emotion arc progression."""
from prosody_manager import ProsodyManager, Emotion

manager = ProsodyManager()
manager.apply_emotion_arc([
    Emotion.HAPPY,      # Turn 0: Happy greeting
    Emotion.SURPRISED,  # Turn 1: Surprise at news
    Emotion.SAD,        # Turn 2: Sad realization
    Emotion.HAPPY,      # Turn 3: Positive resolution
])

# Generate each turn with automatic emotion from arc
for turn_idx, (speaker, text) in enumerate(turns):
    prosody = manager.get_turn_prosody(turn_idx)
    print(f"Turn {turn_idx}: {prosody.emotion.value} - {text}")
```

---

### Task 4.2: Create integration tests

**File**: `tests/test_device_detection.py`
```python
"""Test device detection on different environments."""
import pytest
from device_manager import get_device_info, detect_environment

def test_environment_detection():
    env = detect_environment()
    assert 'is_colab' in env
    assert 'is_linux' in env or env['is_windows'] or env['is_macos']

def test_device_info_has_required_fields():
    device_info = get_device_info()
    assert device_info.device_type in ['cuda', 'cpu', 'mps']
    assert device_info.device_name
    assert device_info.cpu_count > 0

@pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU not available")
def test_gpu_detection():
    device_info = get_device_info(prefer_gpu=True)
    assert device_info.device_type == 'cuda'
    assert device_info.total_memory_mb is not None

def test_cpu_fallback():
    device_info = get_device_info(prefer_gpu=False)
    assert device_info.device_type == 'cpu'
```

---

## 🚀 Implementation Order

```
Day 1 (4 hours):
  ✓ Task 1.1: device_manager integration
  ✓ Task 1.2: memory_optimizer integration  
  ✓ Task 1.3: config option for prefer_gpu
  ✓ Test on Colab GPU and local CPU

Day 2 (3 hours):
  ✓ Fix any Phase 1 issues
  ✓ Document Phase 1 improvements
  ✓ Performance benchmarking

Day 3-4 (6 hours):
  ✓ Task 2.1: Update models.py
  ✓ Task 2.2: Create /v2 endpoint
  ✓ Test all endpoints

Day 5-6 (6 hours):
  ✓ Task 3.1: Error hierarchy
  ✓ Retry logic implementation
  ✓ Graceful degradation

Day 7-9 (9 hours):
  ✓ Task 4.1: Example scripts
  ✓ Task 4.2: Integration tests
  ✓ Complete type hints & docstrings
```

---

## ✅ Verification Checklist

### After Phase 1
- [ ] `python -c "from device_manager import *; get_device_info()"` works
- [ ] `python -c "from memory_optimizer import *; MemoryOptimizer('cpu')"` works
- [ ] Colab detects T4 GPU correctly
- [ ] Local machine detects CPU
- [ ] Config option `device.prefer_gpu` exists and works
- [ ] Memory stats logged at startup and post-generation
- [ ] No performance regressions from Phase 0

### After Phase 2
- [ ] `/v2/audio/speech` endpoint exists and is documented
- [ ] Prosody parameters accepted and applied
- [ ] Emotion arc works for multi-turn generation
- [ ] Backward compatibility maintained for `/v1` endpoints

### After Phase 3
- [ ] Custom errors raised and caught appropriately
- [ ] Retry logic works for transient errors
- [ ] Graceful degradation when optional features fail
- [ ] Error messages are actionable

### After Phase 4
- [ ] All functions have type hints
- [ ] All public functions have docstrings
- [ ] Example scripts run without errors
- [ ] 80%+ test coverage
- [ ] API docs auto-generated from docstrings

---

## 📞 Support Notes

- **Device issues**: Check `device_manager.log_device_info()` output
- **Memory issues**: Check `memory_optimizer.log_memory_status()` output
- **Prosody issues**: Check `prosody_manager.ProsodyProfile.to_prefix()` output
- **API issues**: Check `/docs` auto-generated documentation

---

**Status**: Ready for Implementation  
**Last Updated**: October 16, 2025
