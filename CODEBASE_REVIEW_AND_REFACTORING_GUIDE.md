# CODEBASE_REVIEW_AND_REFACTORING_GUIDE.md

## Executive Summary

This document provides a comprehensive review of the Dia-TTS-Server codebase and a detailed refactoring plan to support both Google Colab (with T4 GPU) and local CPU environments.

## 1. Current Architecture Assessment

### Strengths
- **Modular design**: Core generation logic separated in `engine.py`, web interface in `server.py`, utilities in `utils.py`
- **Configuration-driven**: Uses `config.py` with YAML support for flexible deployment
- **Error handling**: Try-catch blocks around critical operations
- **Type hints**: Partial type annotations present in most files
- **Async support**: FastAPI with async endpoints for non-blocking I/O

### Issues & Limitations

#### 1.1 Device Management
**Current Issue**: `get_device()` forces CPU-only mode regardless of available GPU
```python
def get_device() -> torch.device:
    logger.info("Forcing CPU device selection (CPU-only target environment).")
    return torch.device("cpu")
```

**Impact**: 
- Colab users with T4 GPU cannot leverage GPU acceleration
- Model loading and generation run at CPU speeds on powerful hardware
- 10-50x slowdown compared to GPU inference

**Solution**: Create smart device detection that respects environment
- **File**: `device_manager.py` ✅ CREATED
- Automatically detects Colab vs local environment
- Prefers GPU when available, falls back to CPU
- Logs device capabilities and memory

#### 1.2 Memory Management
**Current Issue**: No adaptive memory management for different device types
- CPU environments (esp. low-memory laptops) may run out of RAM during model loading
- No quantization or dynamic batch sizing
- GPU memory not profiled or optimized

**Solution**: Create memory optimization framework
- **File**: `memory_optimizer.py` ✅ CREATED
- Device-aware memory configuration
- Support for int8/int4 quantization on CPU
- Memory profiling and logging
- Adaptive batch sizing based on available RAM

#### 1.3 Prosody & Emotion Control
**Current Issue**: Limited support for expressive multi-speaker generation
- No emotion types or speaking style enums
- No speaker profiles or preset management
- Emotion/rate passed as strings in API, no structured format
- No support for emotion arcs (emotion progression across turns)

**Solution**: Create comprehensive prosody system
- **File**: `prosody_manager.py` ✅ CREATED
- Enum-based emotions and speaking styles
- Speaker profiles with default prosody
- Prosody presets (enthusiastic, calm, sad, angry, etc.)
- Emotion arc support for natural dialogue progression
- Prefix generation for model input

#### 1.4 Error Handling & Recovery
**Current Issue**: Errors not categorized; no retry logic
- No distinction between transient (network, temp resource) and permanent errors
- Failed generation doesn't provide hints for recovery
- No graceful degradation if optional features fail

**Recommendations**:
- Categorize errors: `TransientError`, `PermanentError`, `ResourceError`
- Add retry logic with exponential backoff for transient errors
- Provide actionable error messages with recovery hints
- Implement fallback generation if cloning fails

#### 1.5 Type Annotations & Documentation
**Current Issue**: Incomplete type hints and sparse docstrings
- Many functions lack return type annotations
- Docstrings don't follow standard format
- API endpoint parameters inconsistently documented

**Solution**: 
- Add comprehensive type hints to all public functions
- Use Google-style docstrings for consistency
- Generate auto-docs from docstrings

#### 1.6 Performance Profiling
**Current Issue**: No built-in latency/throughput metrics
- Difficult to benchmark improvements
- No per-device performance comparison
- Memory usage not tracked systematically

**Solution**: Create performance profiler
- Measure generation latency per device type
- Track memory peaks during generation
- Profile different batch sizes
- Log optimization recommendations

---

## 2. New Modules Created

### 2.1 `device_manager.py`
**Purpose**: Smart device detection and management for GPU/CPU/MPS

**Key Classes/Functions**:
- `DeviceInfo`: Dataclass with device details (type, name, memory, compute capability)
- `detect_environment()`: Identifies Colab, Kaggle, Docker, OS
- `get_device_info(prefer_gpu=True)`: Returns DeviceInfo with auto-detection
- `get_optimal_dtype(device_info, weights_filename)`: Selects optimal precision (fp32, fp16, bf16)
- `get_optimal_device(prefer_gpu=True)`: Returns torch.device with intelligent selection

**Usage**:
```python
from device_manager import get_device_info, get_optimal_dtype, log_device_info

device_info = get_device_info(prefer_gpu=True)  # Auto-detect GPU/CPU
log_device_info(device_info)
dtype = get_optimal_dtype(device_info, "dia-v0_1_bf16.safetensors")
```

### 2.2 `memory_optimizer.py`
**Purpose**: Memory profiling and optimization for different device types

**Key Classes/Functions**:
- `MemoryConfig`: Dataclass with optimization settings
- `MemoryOptimizer`: Main class for device-specific memory management
  - `get_recommended_config()`: Returns optimal config for device type
  - `cleanup_memory()`: Aggressive garbage collection + GPU cache clear
  - `get_memory_usage_mb()`: Current memory stats
  - `log_memory_status()`: Log memory info
- `estimate_model_memory_mb()`: Estimate model memory requirements

**Usage**:
```python
from memory_optimizer import MemoryOptimizer, MemoryConfig

optimizer = MemoryOptimizer(device_type='cuda')
config = optimizer.get_recommended_config()
# Use config.enable_activation_checkpointing, config.quantization_method, etc.

optimizer.cleanup_memory()
usage = optimizer.get_memory_usage_mb()
print(f"Current memory: CPU={usage['cpu_mb']:.1f}MB, GPU={usage['gpu_mb']:.1f}MB")
```

### 2.3 `prosody_manager.py`
**Purpose**: Structured prosody, emotion, and speaker profile management

**Key Classes/Functions**:
- `Emotion`: Enum (NEUTRAL, HAPPY, SAD, ANGRY, SURPRISED, FEARFUL)
- `SpeakingStyle`: Enum (NORMAL, FORMAL, CASUAL, WHISPER, SHOUTING)
- `ProsodyProfile`: Dataclass with rate, pitch, energy, emotion, style, pause_ms
  - `to_prefix()`: Convert to model input prefix
- `ProsodyPreset`: Predefined presets (enthusiastic, calm, energetic, sad, angry, whisper)
- `SpeakerProfile`: Full speaker definition with voice and default prosody
- `ProsodyManager`: Main manager for multi-speaker scenarios
  - `register_speaker()`: Register speaker profiles
  - `apply_emotion_arc()`: Set emotion progression across turns
  - `get_turn_prosody()`: Get prosody for specific turn with arc consideration
  - `build_turn_text()`: Build formatted turn with speaker tag + prosody

**Usage**:
```python
from prosody_manager import ProsodyManager, SpeakerProfile, ProsodyProfile, Emotion

manager = ProsodyManager()

# Create speaker profiles
s1 = SpeakerProfile(
    speaker_id='S1',
    default_prosody=ProsodyProfile(rate=1.0, emotion=Emotion.HAPPY),
    name='Alice'
)
manager.register_speaker(s1)

# Set emotion arc: happy → sad → angry
manager.apply_emotion_arc([Emotion.HAPPY, Emotion.SAD, Emotion.ANGRY])

# Get prosody for turn 1 (will be SAD)
turn_prosody = manager.get_turn_prosody(1)

# Build formatted text
formatted_text = manager.build_turn_text('S1', 'Hello there!', turn_prosody)
# Output: "[S1] [sad] Hello there!"
```

---

## 3. Refactoring Plan (Priority Order)

### Phase 1: Core Integration (High Priority)
**Goal**: Make app work optimally on both Colab GPU and local CPU

1. **Integrate device_manager into engine.py**
   - Replace `get_device()` with smart detection
   - Add config option `prefer_gpu` (default: True for Colab, False for local override)
   - Log device info at startup
   - **Estimated**: 1-2 hours

2. **Integrate memory_optimizer into engine.py**
   - Create MemoryOptimizer at startup based on device type
   - Apply memory config to model loading
   - Call cleanup between generations
   - **Estimated**: 2-3 hours

3. **Enhance generate_speech() signature**
   - Add `prosody: Optional[ProsodyProfile]` parameter
   - Add `speaker_id: Optional[str]` for multi-speaker
   - Maintain backward compatibility
   - **Estimated**: 1-2 hours

### Phase 2: API Enhancements (Medium Priority)
**Goal**: Support new prosody and emotion features in REST API

1. **Update `/tts` endpoint**
   - Add `prosody` parameter (dict with rate, pitch, energy, emotion, style)
   - Add `speaker_id` parameter
   - Support `emotion_arc` array for multi-turn generation
   - **Estimated**: 2-3 hours

2. **Create `/v2/audio/speech` endpoint**
   - Enhanced OpenAI-compatible endpoint with emotion/prosody support
   - Backward compatible with `/v1/audio/speech`
   - **Estimated**: 1-2 hours

3. **Add preset management endpoints**
   - GET `/presets` - list available prosody/speaker presets
   - POST `/presets/custom` - save custom preset
   - DELETE `/presets/{name}` - delete custom preset
   - **Estimated**: 2-3 hours

### Phase 3: Error Handling & Robustness (Medium Priority)
**Goal**: Graceful error handling and recovery

1. **Create error hierarchy**
   - Base `DiaError` class
   - `TransientError` (retry-able: network, temp resource)
   - `PermanentError` (not retry-able: config, invalid input)
   - `ResourceError` (memory, disk space)
   - **Estimated**: 1-2 hours

2. **Implement retry logic**
   - Exponential backoff for transient errors (3 attempts by default)
   - Configurable retry strategy
   - **Estimated**: 1-2 hours

3. **Add graceful degradation**
   - If cloning fails, fall back to S1/S2 generation
   - If GPU memory insufficient, downgrade dtype precision
   - Log warnings but continue
   - **Estimated**: 2-3 hours

### Phase 4: Documentation & Testing (Lower Priority)
**Goal**: Comprehensive docs and test coverage

1. **Add type hints & docstrings**
   - Complete all public function signatures with types
   - Add Google-style docstrings to all modules
   - **Estimated**: 2-3 hours

2. **Create example scripts**
   - `examples/simple_dialog.py` - multi-turn dialogue
   - `examples/emotion_arc.py` - emotion progression
   - `examples/voice_cloning.py` - custom voice generation
   - `examples/preset_usage.py` - using prosody presets
   - **Estimated**: 2-3 hours

3. **Build integration test suite**
   - Test device detection (GPU/CPU/MPS)
   - Test memory optimization
   - Test prosody application
   - Test multi-speaker generation
   - Test error handling
   - **Estimated**: 3-4 hours

4. **Generate API documentation**
   - Document all endpoints with examples
   - Generate OpenAPI schema
   - Create usage guide for common scenarios
   - **Estimated**: 2-3 hours

---

## 4. Configuration Changes

### Current config.yaml Structure
```yaml
server:
  host: "0.0.0.0"
  port: 8003

model:
  repo_id: "nari-labs/Dia-1.6B"
  config_filename: "config.json"
  weights_filename: "dia-v0_1.safetensors"
```

### Proposed Additions
```yaml
device:
  prefer_gpu: true           # Use GPU if available (Colab T4)
  force_cpu: false           # Override to CPU only
  auto_detect: true          # Auto-detect environment

memory:
  enable_optimization: true
  quantization: auto         # auto, int8, int4, none
  max_memory_mb: null        # Limit memory usage (null = unlimited)
  profile_memory: false      # Log memory usage

generation:
  default_prosody:
    rate: 1.0
    pitch: 0.0
    energy: 1.0
    emotion: "neutral"
    style: "normal"
```

---

## 5. Quick Start: Using New Modules

### Example 1: Simple Generation on Any Device
```python
from device_manager import get_device_info, get_optimal_device, get_optimal_dtype
from memory_optimizer import MemoryOptimizer
import engine

# Smart device detection
device_info = get_device_info(prefer_gpu=True)
device = get_optimal_device(prefer_gpu=True)
dtype = get_optimal_dtype(device_info, "dia-v0_1_bf16.safetensors")

# Memory optimization
optimizer = MemoryOptimizer(device_info.device_type)
memory_config = optimizer.get_recommended_config()

# Use in engine
audio, sr = engine.generate_speech(text="Hello!", device=device, dtype=dtype)
```

### Example 2: Multi-Speaker Dialogue with Emotion Arc
```python
from prosody_manager import ProsodyManager, SpeakerProfile, ProsodyProfile, Emotion

manager = ProsodyManager()

# Create characters
alice = SpeakerProfile(
    speaker_id='S1',
    name='Alice',
    default_prosody=ProsodyProfile(rate=1.0, emotion=Emotion.HAPPY)
)
bob = SpeakerProfile(
    speaker_id='S2',
    name='Bob',
    default_prosody=ProsodyProfile(rate=0.95, emotion=Emotion.NEUTRAL)
)

manager.register_speaker(alice)
manager.register_speaker(bob)

# Define emotion arc: excitement → confusion → resolution
manager.apply_emotion_arc([Emotion.HAPPY, Emotion.SURPRISED, Emotion.HAPPY])

# Generate dialogue
dialogue = [
    ("S1", "I have great news!"),
    ("S2", "What? Tell me more!"),
    ("S1", "We won the lottery!"),
]

for turn_idx, (speaker, text) in enumerate(dialogue):
    prosody = manager.get_turn_prosody(turn_idx)
    formatted = manager.build_turn_text(speaker, text, prosody)
    print(formatted)
    # Generate audio for formatted text
```

### Example 3: Cloning with Prosody
```python
from prosody_manager import ProsodyProfile, Emotion
import engine

# Clone voice with different emotions
reference_audio = "reference/alice.wav"
reference_text = "[S1] Hello, my name is Alice."

emotions = [Emotion.HAPPY, Emotion.SAD, Emotion.ANGRY]

for emotion in emotions:
    prosody = ProsodyProfile(emotion=emotion, rate=1.0)
    
    audio, sr = engine.generate_speech(
        text="I love this product!",
        voice_mode="clone",
        clone_reference_filename=reference_audio,
        transcript=reference_text,
        prosody=prosody
    )
    
    engine.save_audio_to_file(audio, sr, f"output_{emotion.value}.wav")
```

---

## 6. Performance Expectations

### Current (CPU-only)
- Model loading: ~30-60 seconds on CPU
- Generation: ~10-20 seconds for 10 seconds of audio
- Memory: ~4-6 GB RAM

### After GPU Optimization (Colab T4)
- Model loading: ~5-10 seconds
- Generation: ~1-3 seconds for 10 seconds of audio
- Memory: ~2-4 GB VRAM (out of 16GB available)

### After Memory Optimization (Local CPU)
- Model loading: ~30 seconds (same)
- Generation: ~10 seconds (same, but with int8 quantization)
- Memory: ~2-3 GB RAM (30-40% reduction)

---

## 7. Testing Checklist

- [ ] Device detection works on Colab with T4 GPU
- [ ] Device detection works on local CPU
- [ ] Memory profiler logs accurate stats
- [ ] GPU memory doesn't exceed 8GB on Colab
- [ ] CPU memory doesn't exceed 4GB on local
- [ ] Prosody presets apply correctly
- [ ] Emotion arc progresses through turns
- [ ] Multi-speaker dialogue maintains continuity
- [ ] Voice cloning with prosody works
- [ ] API endpoints return correct formats
- [ ] Error messages are actionable
- [ ] Retry logic works for transient errors

---

## 8. File Dependencies

### New Module Imports
```
device_manager.py
  └─ torch, psutil, logging

memory_optimizer.py
  └─ torch, psutil, gc, logging

prosody_manager.py
  └─ dataclasses, enum, typing, logging

engine.py (after refactoring)
  ├─ device_manager
  ├─ memory_optimizer
  └─ prosody_manager

server.py (after refactoring)
  ├─ device_manager (for startup logging)
  └─ prosody_manager (for API serialization)
```

---

## 9. Next Steps

1. **Review this document** with team/stakeholders
2. **Install new modules** (psutil may need adding to requirements.txt)
3. **Begin Phase 1 integration** (device + memory managers)
4. **Test on both Colab and local CPU**
5. **Proceed with Phase 2** (API enhancements)
6. **Complete Phases 3-4** (error handling, docs, tests)

---

**Generated**: October 16, 2025
**Status**: Ready for Implementation
**Estimated Total Time**: 20-25 hours across all phases
