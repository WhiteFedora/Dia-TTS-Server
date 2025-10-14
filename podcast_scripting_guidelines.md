# Podcast Scripting Guidelines for Dia TTS Server

## Introduction

The Dia TTS Server provides advanced text-to-speech capabilities specifically designed for generating natural conversational dialogue between multiple speakers. This system leverages the Dia model to create high-quality audio for podcast-style content, interviews, and scripted conversations.

### Key Features
- **Multi-speaker dialogue generation** with distinct voice characteristics
- **Prosody control** for emotional expression and natural speech patterns
- **Voice cloning** from reference audio samples
- **Predefined voice pairs** for consistent speaker personalities
- **Real-time audio processing** with post-processing enhancements

### System Architecture
The server consists of:
- FastAPI-based REST API endpoints
- Dia model integration for speech synthesis
- Web UI for interactive generation
- Audio post-processing pipeline (silence trimming, normalization)
- Voice cloning capabilities using reference audio

## Setup and Configuration

### Server Installation
```bash
# Clone the repository
git clone https://github.com/devnen/dia-tts-server.git
cd dia-tts-server

# Install dependencies
pip install -r requirements.txt

# Download the Dia model
python download_model.py

# Start the server
python server.py
```

### Configuration Files
The server uses YAML-based configuration (`config.yaml`) for:
- Model paths and repository IDs
- Audio processing parameters
- Voice directories
- Generation defaults

### API Endpoints
- `/tts` - Custom TTS endpoint for full parameter control
- `/v1/audio/speech` - OpenAI-compatible endpoint
- `/web/generate` - Web UI generation endpoint

## Dialogue Formatting Rules

### Speaker Tags
Use bracketed speaker identifiers to distinguish between speakers:

```
[S1] Hello, I'm the first speaker.
[S2] And I'm the second speaker.
[S1] Great to meet you!
```

### Prosody Markers
Control speech characteristics using special markers:

- `[PAUSE]` - Insert a brief pause (0.5-1 second)
- `[EMO=happy]` - Set emotional tone
- `[RATE=0.8]` - Adjust speaking rate (0.5-2.0)
- `(laughs)` - Parenthetical actions or sounds
- `(sighs)` - Emotional expressions

### Text Splitting
The system automatically splits long text into chunks for processing:
- Default chunk size: 300 characters
- Speaker tag boundaries respected
- Configurable via API parameters

## Natural Conversation Elements

### Verbal Tics and Fillers
```
[S1] Well, you know, um... [PAUSE] that's really interesting.
[S2] Yeah, exactly! I mean, wow.
[S1] Right? Like, totally.
```

### Interruptions and Overlaps
```
[S1] I was thinking that we should--
[S2] [EMO=interrupted] Wait, hold on! That's not right.
[S1] Let me finish my thought first.
```

### Pacing Variations
```
[S1] [RATE=0.7] This is a slow, deliberate explanation...
[S2] [RATE=1.3] And this is fast and excited!
[S1] [RATE=1.0] Back to normal pace now.
```

### Emotional Variations
```
[S1] [EMO=calm] Everything is fine.
[S2] [EMO=excited] This is amazing!
[S1] [EMO=sad] I'm disappointed.
[S2] [EMO=angry] That's unacceptable!
```

## Audio Rendering Process

### Voice Mode Selection
1. **Dialogue Mode**: Random voices for each speaker tag
2. **Predefined Voices**: Consistent voices from voice library
3. **Voice Cloning**: Custom voices from reference audio

### Generation Parameters
```python
{
    "text": "[S1] Hello [S2] Hi there",
    "voice_mode": "dialogue",
    "speed_factor": 0.94,
    "cfg_scale": 3.0,
    "temperature": 1.3,
    "split_text": True,
    "chunk_size": 300
}
```

### Post-Processing Pipeline
1. **Silence trimming** - Remove leading/trailing silence
2. **Internal silence fix** - Reduce long pauses
3. **Speed adjustment** - Apply rate modifications
4. **Normalization** - Ensure consistent audio levels

## Error Handling and Validation

### Common Issues
- **Missing speaker tags**: Default to [S1] if none specified
- **Invalid voice files**: Fallback to dialogue mode
- **Long text chunks**: Automatic splitting with warnings
- **Audio encoding failures**: Retry with different formats

### Validation Rules
- Speaker tags must be [S1], [S2], etc.
- Reference files must exist in configured directory
- Text length limited by chunk_size parameter
- Audio format must be WAV or Opus

### Error Responses
```json
{
    "detail": "Reference audio file not found: example.wav",
    "status_code": 404
}
```

## Best Practices

### Coherence and Flow
- Use consistent speaker tags throughout
- Maintain logical conversation flow
- Include natural transitions between speakers
- Balance dialogue length between speakers

### Speaker Personality
- Assign distinct personalities to each speaker
- Use prosody markers to reinforce character traits
- Maintain consistent emotional arcs
- Consider cultural and regional speech patterns

### Ethical Considerations
- Avoid harmful stereotypes in character voices
- Respect privacy when using voice cloning
- Consider accessibility needs for generated content
- Label AI-generated content appropriately

## Code Examples

### Basic Dialogue
```python
import requests

url = "http://localhost:8080/tts"
data = {
    "text": "[S1] Hello, how are you today? [S2] I'm doing well, thank you! How about you?",
    "voice_mode": "dialogue",
    "output_format": "wav"
}

response = requests.post(url, json=data)
with open("dialogue.wav", "wb") as f:
    f.write(response.content)
```

### Emotional Conversation
```python
data = {
    "text": "[S1] [EMO=excited] I just won the lottery! [S2] [EMO=shocked] No way! That's amazing! [S1] [EMO=happy] I know, right? (laughs)",
    "voice_mode": "predefined",
    "predefined_voice": "Abigail_Taylor.wav",
    "speed_factor": 1.1
}
```

### Interruptions and Overlaps
```python
data = {
    "text": "[S1] Let me tell you about-- [S2] [EMO=interrupted] Wait! I have something important to say first. [S1] Okay, go ahead. [PAUSE] [S2] Thanks. So the thing is...",
    "voice_mode": "clone",
    "clone_reference_filename": "host.wav",
    "split_text": True
}
```

### Pacing Variations
```python
data = {
    "text": "[S1] [RATE=0.8] Let me explain this slowly... [PAUSE] The key point is understanding the basics first. [S2] [RATE=1.4] Got it! So then what happens next? [S1] [RATE=1.0] Well, then we move to the next step.",
    "temperature": 1.1,
    "cfg_scale": 2.5
}
```

### Speaker Personality Differences
```python
# Host (calm, measured)
host_text = "[S1] [EMO=calm] Welcome to our show today. [RATE=0.9] We're discussing artificial intelligence."

# Guest (enthusiastic, fast-paced)
guest_text = "[S2] [EMO=excited] Absolutely! [RATE=1.2] AI is changing everything!"

data = {
    "text": host_text + " " + guest_text,
    "voice_mode": "dialogue",
    "turns": [
        {"speaker": "S1", "text": "Welcome to our show today. We're discussing artificial intelligence.", "emotion": "calm", "rate": 0.9},
        {"speaker": "S2", "text": "Absolutely! AI is changing everything!", "emotion": "excited", "rate": 1.2}
    ]
}
```

## Advanced Features

### Multi-turn Structures
```python
turns = [
    {"speaker": "S1", "text": "First point", "emotion": "calm", "rate": 1.0, "pause_after": 0.5},
    {"speaker": "S2", "text": "Counter point", "emotion": "skeptical", "rate": 1.1},
    {"speaker": "S1", "text": "Rebuttal", "emotion": "confident", "rate": 0.95}
]

data = {
    "turns": turns,
    "voice_mode": "dialogue"
}
```

### Voice Cloning
```python
# Using reference audio
data = {
    "text": "[S1] This is my cloned voice.",
    "voice_mode": "clone",
    "clone_reference_filename": "my_voice.wav",
    "transcript": "This is a sample of my voice for cloning."
}
```

### Batch Processing
```python
# Process multiple dialogue segments
segments = [
    "[S1] Opening statement",
    "[S2] Response",
    "[S1] Follow-up"
]

for segment in segments:
    data = {"text": segment, "voice_mode": "dialogue"}
    # Process each segment
```

### Custom Voice Pairs
```python
# Use predefined voice pairs for consistency
data = {
    "text": "[S1] Host speaking [S2] Guest responding",
    "voice_mode": "predefined",
    "clone_reference_filename": "Host_Guest.wav"  # Paired voice file
}
```

This comprehensive guide covers all aspects of creating natural, engaging podcast content with the Dia TTS Server. The system's flexibility allows for everything from simple dialogues to complex multi-speaker conversations with rich emotional expression and natural speech patterns.