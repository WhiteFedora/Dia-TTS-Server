# Architecture & Data Flow

## Current Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      Dia-TTS-Server                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  server.py   │───▶│  engine.py   │───▶│   dia/       │  │
│  │  (FastAPI)   │    │ (Generation) │    │  (Model)     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│       △                      △                                │
│       │                      │                                │
│       └──────────────────────┤                                │
│         models.py            │                                │
│         (Schemas)            │                                │
│                              │                                │
│                   ┌──────────▼──────────┐                    │
│                   │   config.py          │                    │
│                   │  (Configuration)     │                    │
│                   └─────────────────────┘                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Proposed Enhanced Architecture
```
┌──────────────────────────────────────────────────────────────────┐
│                     Dia-TTS-Server Enhanced                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐         ┌──────────────┐         ┌───────────┐ │
│  │  server.py   │────────▶│  engine.py   │────────▶│  dia/     │ │
│  │  (FastAPI)   │         │ (Generation) │         │  (Model)  │ │
│  └──────────────┘         └──────────────┘         └───────────┘ │
│       △                         △                                  │
│       │                         │                                  │
│  ┌────┴─────────────────────────┴───────────────────────────┐    │
│  │              Configuration & State Management             │    │
│  ├──────────────────────────────────────────────────────────┤    │
│  │                                                            │    │
│  │  ┌──────────────────┐  ┌──────────────────┐             │    │
│  │  │  device_manager  │  │ memory_optimizer │             │    │
│  │  │  (NEW)           │  │ (NEW)            │             │    │
│  │  ├──────────────────┤  ├──────────────────┤             │    │
│  │  │ detect_env()     │  │ get_memory_usage │             │    │
│  │  │ get_device_info()│  │ cleanup_memory() │             │    │
│  │  │ get_optimal_*()  │  │ get_recommended_ │             │    │
│  │  └──────────────────┘  │   config()       │             │    │
│  │                        └──────────────────┘             │    │
│  │                                                          │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │        prosody_manager (NEW)                     │  │    │
│  │  ├──────────────────────────────────────────────────┤  │    │
│  │  │ • ProsodyProfile (rate, pitch, energy, emotion) │  │    │
│  │  │ • SpeakerProfile (voice + default prosody)      │  │    │
│  │  │ • ProsodyPreset (enthusiastic, calm, etc)       │  │    │
│  │  │ • ProsodyManager (emotion arcs, formatting)     │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │                                                          │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐   │    │
│  │  │  config.py   │  │  models.py   │  │ utils.py   │   │    │
│  │  │   (Config)   │  │  (Schemas)   │  │ (Helpers)  │   │    │
│  │  └──────────────┘  └──────────────┘  └────────────┘   │    │
│  │                                                          │    │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │   Error Handling & Performance (Phase 3-4)                   ││
│  ├──────────────────────────────────────────────────────────────┤│
│  │  • errors.py (DiaError hierarchy)                            ││
│  │  • performance_profiler.py (latency & memory metrics)        ││
│  │  • Retry logic with exponential backoff                      ││
│  │  • Graceful degradation for optional features                ││
│  └──────────────────────────────────────────────────────────────┘│
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow: Single Speaker Generation
```
User Request
     │
     ▼
┌─────────────────────────────────┐
│  server.py: /v1/audio/speech    │
│  (OpenAI-compatible)            │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ Parse & Validate Request        │
│ • Map voice parameter to mode   │
│ • Check device ready            │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ engine.generate_speech()        │
│ • Load device_info              │
│ • Select dtype via device_mgr   │
│ • Prepare text                  │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ Model Generation                │
│ • dia.generate()                │
│ • memory_optimizer cleanup()    │
│ • Post-processing               │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ Encode Audio                    │
│ • WAV or Opus format            │
└─────────────────────────────────┘
     │
     ▼
StreamingResponse (audio bytes)
```

## Data Flow: Multi-Speaker with Emotion Arc
```
User Request (multi-turn dialogue)
     │
     ▼
┌─────────────────────────────────┐
│ Parse speaker profiles          │
│ Register with prosody_manager   │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ Apply emotion arc               │
│ prosody_manager.apply_emotion_  │
│   arc([HAPPY, SAD, ANGRY])      │
└─────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────┐
│ For each turn:                  │
│ 1. Get turn prosody from arc    │
│ 2. Build formatted text         │
│ 3. Call generate_speech()       │
│ 4. Concatenate audio chunks     │
└─────────────────────────────────┘
     │
     ▼
Combined Audio Output
```

## Device Selection Logic
```
User Code / Config (prefer_gpu=True/False)
     │
     ▼
┌─────────────────────────────────┐
│ device_manager.get_device_info()│
└─────────────────────────────────┘
     │
     ├─ Is Colab?
     │   ├─ Yes → Check GPU available
     │   │   ├─ Yes → Return CUDA (T4 GPU)
     │   │   └─ No → Return CPU
     │   └─ No → Check GPU available (prefer_gpu)
     │       ├─ Yes → Return CUDA
     │       ├─ No → Check MPS available
     │       │   ├─ Yes → Return MPS (Apple Metal)
     │       │   └─ No → Return CPU
     │
     ▼
torch.device ('cuda', 'mps', or 'cpu')
     │
     ▼
Log device info (capabilities, memory, etc)
```

## Memory Optimization Strategy
```
Device Type Detected
     │
     ├─ CUDA (Colab T4)
     │   └─ MemoryConfig:
     │       ├─ use_mixed_precision: True
     │       ├─ quantization: None (FP32/FP16)
     │       ├─ max_memory: Unlimited
     │       └─ profile_memory: True
     │
     ├─ CPU (Low Memory)
     │   └─ MemoryConfig:
     │       ├─ use_mixed_precision: False
     │       ├─ quantization: int8
     │       ├─ max_memory: 4GB
     │       └─ profile_memory: True
     │
     └─ CPU (Normal)
         └─ MemoryConfig:
             ├─ use_mixed_precision: False
             ├─ quantization: None (FP32)
             ├─ max_memory: Unlimited
             └─ profile_memory: True
```

## Prosody Application Pipeline
```
Input Text + Prosody Profile
     │
     ├─ Extract components:
     │  ├─ Emotion (happy, sad, angry, etc)
     │  ├─ Speaking style (normal, formal, casual, etc)
     │  ├─ Rate (0.5x to 2.0x speed)
     │  ├─ Pitch (+/- semitones)
     │  └─ Energy (volume multiplier)
     │
     ▼
prosody_profile.to_prefix()
     │
     ├─ Generate markup tokens:
     │  ├─ [happy] for emotion
     │  ├─ [formal] for style
     │  ├─ [rate=1.2] for speed
     │  └─ [pitch=+2] for pitch
     │
     ▼
Formatted Text with Prosody Tokens
     │
     ├─ Example output:
     │  "[S1] [happy] [rate=1.2] Hello, I'm excited!"
     │
     ▼
Pass to model.generate()
     │
     ▼
Audio with Applied Prosody
```

## Error Handling Flow (Phase 3)
```
generate_speech() called
     │
     ▼
Try to load model
     ├─ Catch OOM → ResourceError → Clean memory → Retry
     ├─ Catch invalid config → PermanentError → Fail with hint
     ├─ Catch network timeout → TransientError → Retry with backoff
     └─ Catch other → Log, attempt graceful degradation
     │
     ▼
Try voice cloning (if enabled)
     ├─ Catch missing transcript → Try Whisper
     ├─ Catch Whisper timeout → TransientError → Retry
     ├─ Catch cloning failure → PermanentError → Fall back to S1/S2
     └─ Success → Continue
     │
     ▼
Generate audio
     ├─ Catch OOM → Free memory → Reduce precision → Retry
     ├─ Catch timeout → TransientError → Retry
     └─ Success → Continue
     │
     ▼
Return audio or actionable error message
```

## Module Dependency Graph
```
server.py
  ├─ device_manager.py
  │   └─ torch, psutil
  ├─ memory_optimizer.py
  │   └─ torch, psutil, gc
  ├─ prosody_manager.py
  │   └─ dataclasses, enum
  ├─ models.py
  │   └─ pydantic
  ├─ engine.py
  │   ├─ device_manager.py
  │   ├─ memory_optimizer.py
  │   ├─ prosody_manager.py
  │   ├─ dia/
  │   ├─ config.py
  │   └─ utils.py
  └─ config.py
      └─ PyYAML, pydantic, python-dotenv

tests/
  ├─ test_device_detection.py
  │   └─ device_manager.py
  ├─ test_memory_optimization.py
  │   └─ memory_optimizer.py
  ├─ test_prosody_manager.py
  │   └─ prosody_manager.py
  └─ test_integration.py
      ├─ engine.py
      ├─ server.py
      └─ All modules
```

## API Endpoint Evolution
```
Current (v1):
  POST /v1/audio/speech
  POST /tts
  
After Phase 2 (v2):
  POST /v1/audio/speech          (backward compatible)
  POST /v2/audio/speech          (with prosody/emotion)
  POST /tts                        (backward compatible)
  GET  /presets                    (list prosody presets)
  POST /presets/custom             (save custom preset)
  GET  /speakers                   (list speaker profiles)
  POST /speakers                   (register speaker)
  
After Phase 3 (error handling):
  All endpoints return structured errors with recovery hints
  
After Phase 4 (full docs):
  /docs                            (auto-generated OpenAPI)
  /redoc                           (ReDoc docs)
```

---

**This architecture supports:**
✅ Both Colab (T4 GPU) and local CPU environments  
✅ Automatic device and memory optimization  
✅ Multi-speaker dialogue with natural emotion arcs  
✅ Voice cloning with full prosody control  
✅ Graceful error handling and recovery  
✅ Comprehensive type hints and documentation  
✅ Extensible preset system for common use cases  
