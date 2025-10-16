# Dia TTS Examples

This directory contains example scripts demonstrating the capabilities of the Dia TTS Server.

## Getting Started

1. **Start the server** (if not already running):
   ```bash
   cd ..
   python server.py
   ```

2. **Run an example**:
   ```bash
   python example_1_simple_dialogue.py
   ```

3. **Find generated audio** in the created `generated_audio/` directory

## Examples

### Example 1: Simple Dialogue Generation
**File**: `example_1_simple_dialogue.py`

Demonstrates basic multi-speaker dialogue generation with [S1] and [S2] tags.

**Key Features**:
- Basic dialogue syntax ([S1], [S2] tags)
- Text splitting for long passages
- Standard generation parameters

**Run it**:
```bash
python example_1_simple_dialogue.py
```

### Example 2: Advanced Prosody & Emotion Control
**File**: `example_2_prosody.py`

Shows new Phase 2 features for emotional and stylistic speech control.

**Key Features**:
- Emotion selection (happy, sad, angry, surprised, fearful, neutral)
- Speaking styles (normal, formal, casual, whisper, shouting)
- Pitch shifting for voice variation
- Energy level control
- Character voice creation

**Run it**:
```bash
python example_2_prosody.py
```

**Emotions & Styles**:
```python
from example_2_prosody import Emotion, SpeakingStyle

# Available emotions
Emotion.HAPPY
Emotion.SAD
Emotion.ANGRY
Emotion.SURPRISED
Emotion.FEARFUL
Emotion.NEUTRAL

# Available styles
SpeakingStyle.NORMAL
SpeakingStyle.FORMAL
SpeakingStyle.CASUAL
SpeakingStyle.WHISPER
SpeakingStyle.SHOUTING
```

### Example 3: Voice Cloning
**File**: `example_3_voice_cloning.py`

Demonstrates voice cloning using reference audio files.

**Key Features**:
- Clone voices from reference audio
- Auto-transcription with Whisper
- Optional custom transcripts
- Support for .wav and .mp3 formats

**Setup**:
1. Place reference audio files in `../reference_audio/` directory
2. Optionally add `.txt` files with transcripts (same base name)

**Run it**:
```bash
python example_3_voice_cloning.py
```

## API Endpoint Usage

All examples use the `/tts` endpoint. Here's the full request structure:

```python
import requests

payload = {
    # Text & Mode
    "text": "Your text here [S1] or [S2]",
    "voice_mode": "dialogue",  # or "single_s1", "single_s2", "clone"
    "turns": None,  # Optional list of turns with speaker/emotion/rate
    
    # Cloning (if voice_mode="clone")
    "clone_reference_filename": "reference.wav",
    "transcript": None,  # Optional
    
    # Generation Parameters
    "max_tokens": None,
    "cfg_scale": 3.0,
    "temperature": 1.3,
    "top_p": 0.95,
    "speed_factor": 1.0,
    "cfg_filter_top_k": 35,
    "seed": -1,  # -1 for random
    
    # Text Processing
    "split_text": True,
    "chunk_size": 300,
    
    # Prosody (NEW - Phase 2)
    "emotion": "happy",  # or null
    "speaking_style": "casual",  # or null
    "pitch_shift": 0.0,  # -12 to +12 semitones
    "energy_level": 1.0,  # 0.5 to 2.0
    
    # Output
    "output_format": "wav",  # or "opus"
}

response = requests.post("http://localhost:8003/tts", json=payload)
```

## Tips for Best Results

### Dialogue
- Keep lines natural and conversational
- Use proper punctuation
- Vary line lengths
- Break long monologues into multiple lines

### Emotions & Styles
- Combine emotion + style for unique characters
- Pitch shift creates age/gender variations
- Energy level affects vocal dynamics
- Test combinations to find your favorites

### Voice Cloning
- Reference audio: 10-20 seconds works best
- Clear, clean audio produces better results
- Provide transcripts if available
- First run takes longer (Whisper model download)

### Performance
- GPU (Colab T4): ~5-10s model load, 1-3s generation per 10s audio
- CPU (laptop): ~30-60s model load, 10-20s generation per 10s audio
- Use `speed_factor` to adjust output duration post-processing

## Advanced: Using Prosody Profiles

The `prosody_manager.py` module provides programmatic control:

```python
from prosody_manager import ProsodyManager, Emotion, SpeakingStyle, ProsodyProfile

manager = ProsodyManager()

# Create custom profile
profile = ProsodyProfile(
    rate=1.0,
    pitch=2.0,  # Semitones
    energy=1.3,
    emotion=Emotion.HAPPY,
    style=SpeakingStyle.CASUAL,
    pause_ms=400
)

# Get preset profiles
profile = manager.get_preset("enthusiastic")  # Built-in preset
```

## Troubleshooting

### "Connection refused"
- Start the server: `python server.py`
- Check it's running on port 8003

### "Model not loaded"
- Server is still loading the model on startup
- Wait a moment and retry (check logs)

### "Reference file not found"
- Ensure file is in `../reference_audio/`
- Check the exact filename (case-sensitive on Linux/Mac)

### "Request timed out"
- Generation is taking longer than expected
- Model may still be loading
- Increase timeout in example scripts

### "Emotion not working"
- Phase 2 features need the updated API
- Make sure server code is updated
- Try without emotion parameters first

## Contributing

To add your own examples:

1. Create a new file: `example_N_your_feature.py`
2. Include docstrings and comments
3. Test with the running server
4. Add to this README

## FAQ

**Q: Can I run multiple examples at once?**  
A: Yes, but they'll queue due to model lock. Sequential is recommended.

**Q: What languages does it support?**  
A: Primarily English. Other languages may work but are not optimized.

**Q: How do I use this in production?**  
A: See the main README.md for deployment options (Docker, Colab, etc.).

**Q: Can I batch process multiple texts?**  
A: Not in this version, but you can loop through examples.

**Q: How do I save my favorite presets?**  
A: Create custom presets in `prosody_manager.py` or save configs.

---

For more information, see the main README.md and documentation files.
