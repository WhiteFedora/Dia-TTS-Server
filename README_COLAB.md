# 🎵 Dia TTS for Google Colab

A complete Text-to-Speech system powered by the Dia model, fully adapted for Google Colab with GPU support and interactive UI.

## 🚀 Quick Start

### 1. Open in Google Colab
Click the button below to open the notebook in Google Colab:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/your-repo/dia-tts-colab/blob/main/dia_tts_colab.ipynb)

### 2. Run the Installation Cell
Execute the first cell to install all dependencies:
```python
# The installation cell will automatically:
# - Install PyTorch, torchaudio, and other ML libraries
# - Set up the Dia model dependencies
# - Create necessary directories
# - Configure the environment
```

### 3. Load the Model
Run the model loading cell:
```python
# This downloads the ~1.6GB Dia model
# First run may take 5-10 minutes
# Subsequent runs are much faster (cached)
```

### 4. Use the Interactive Interface
The main interface provides:
- **Text Input**: Multi-line text area with formatting help
- **Voice Mode Selection**: Dialogue, Voice Cloning, or Predefined Voices
- **Parameter Controls**: Speed, CFG scale, temperature, and more
- **File Upload**: Upload reference audio for voice cloning
- **Real-time Generation**: Progress bars and status updates
- **Audio Playback**: Built-in player for generated audio

## 🎯 Features

### ✅ Voice Cloning
- Upload reference audio files (.wav/.mp3)
- Create matching transcript files (.txt)
- Clone voices with high fidelity
- Support for multiple reference voices

### ✅ Multi-Speaker Dialogue
- Use `[S1]` and `[S2]` tags for conversations
- Automatic voice differentiation
- Emotion and prosody controls
- Natural dialogue flow

### ✅ Predefined Voices
- Curated voice samples in `/content/dia_tts/voices/`
- Consistent voice generation
- Easy voice selection interface
- Support for voice pairs

### ✅ GPU Acceleration
- Automatic hardware detection (CPU/GPU/MPS)
- Optimized for Google Colab GPUs
- Memory-efficient processing
- Real-time performance monitoring

### ✅ Interactive UI
- Modern web-style interface in Jupyter
- Real-time parameter adjustment
- File upload and management
- Audio playback and download
- Progress tracking

## 📁 File Structure

```
dia_tts_colab.ipynb          # Main notebook
colab_config.py             # Configuration management
colab_files.py              # File management utilities
engine_colab.py             # Core TTS engine (GPU-enabled)
colab_ui.py                 # Interactive user interface
requirements_colab.txt      # Colab-specific dependencies
README_COLAB.md             # This file

/content/dia_tts/
├── models/                 # Downloaded model files (~1.6GB)
├── reference_audio/        # Voice cloning files
│   ├── audio1.wav         # Reference audio
│   ├── audio1.txt         # Matching transcript
│   ├── audio2.wav
│   └── audio2.txt
├── voices/                # Predefined voice samples
│   ├── voice1.wav
│   └── voice2.wav
└── outputs/               # Generated audio files
    ├── generation1.wav
    └── generation2.wav
```

## 🎛️ Usage Examples

### Basic Dialogue Generation
```python
from colab_ui import quick_generate

text = "[S1] Hello! How are you today? [S2] I'm doing great, thanks!"
audio = quick_generate(text, voice_mode="dialogue")
display(audio)
```

### Voice Cloning
```python
# After uploading reference audio and transcript
text = "[S1] This will sound like my reference voice!"
audio = quick_generate(text, voice_mode="clone", clone_reference_filename="my_voice.wav")
display(audio)
```

### Custom Parameters
```python
audio = quick_generate(
    text="Custom voice with specific settings",
    voice_mode="dialogue",
    speed_factor=1.2,
    cfg_scale=3.5,
    temperature=0.8,
    seed=42
)
```

## ⚙️ Configuration

### Hardware Settings
- **Auto Detection**: Automatically uses best available hardware
- **GPU Support**: Enable in Colab Runtime settings for faster generation
- **Memory Management**: Automatic cleanup and optimization

### Model Settings
- **Repository**: `ttj/dia-1.6b-safetensors` (default)
- **Precision**: Automatic BF16/FP16/FP32 selection based on hardware
- **Caching**: Models cached locally for faster subsequent loads

### Generation Parameters
- **Speed Factor**: 0.5-2.0 (affects audio playback speed)
- **CFG Scale**: 1.0-5.0 (higher = more prompt adherence)
- **Temperature**: 0.1-1.5 (higher = more creative)
- **Top P**: 0.1-1.0 (nucleus sampling)
- **Seed**: Integer for reproducible results, -1 for random

## 📝 Text Formatting Guide

### Speaker Tags
```
[S1] Hello, I'm the first speaker.
[S2] Hi there! I'm the second speaker.
[S1] Great to meet you!
```

### Emotions and Sounds
```
[S1] I'm so excited! (excited)
[S2] That's wonderful news. (happy)
[S1] Oh no, that's terrible! (sad)
[S2] Don't worry, it'll be okay. (laughs)
```

### Prosody Controls
```
[S1] [EMO=happy] This is a happy sentence.
[S2] [RATE=0.7] This is a slower sentence.
[S1] [EMO=excited][RATE=1.3] Fast and excited speech!
```

### Pauses and Breaks
```
[S1] Let me think for a moment... (pause=1.0)
[S2] Take your time.
[S1] Okay, I know what to say now!
```

## 🔧 Advanced Usage

### Custom Model Loading
```python
from engine_colab import load_model
from colab_config import update_config

# Use different model
update_config({'model_repo_id': 'custom/dia-model'})
load_model()
```

### Batch Processing
```python
texts = [
    "[S1] First sentence.",
    "[S2] Second sentence.",
    "[S1] Third sentence."
]

for i, text in enumerate(texts):
    audio = quick_generate(text, seed=i)
    # Save or process audio
```

### File Management
```python
from colab_files import get_reference_files, save_uploaded_file

# List available reference files
files = get_reference_files()
print(f"Available files: {files}")

# Upload file programmatically
with open('my_audio.wav', 'rb') as f:
    save_uploaded_file(f.read(), 'my_audio.wav')
```

## 🚨 Troubleshooting

### Common Issues

**❌ Model won't load**
- Check internet connection
- Verify disk space (>2GB free)
- Try restarting runtime

**❌ Poor audio quality**
- Adjust generation parameters
- Use higher CFG scale (2.5-4.0)
- Lower temperature (0.8-1.0)

**❌ Voice cloning not working**
- Ensure transcript file matches audio filename
- Check transcript format (use [S1] tags)
- Verify audio quality and length

**❌ Out of memory errors**
- Reduce chunk size in settings
- Disable GPU if experiencing issues
- Process shorter texts

**❌ File upload issues**
- Check file format (.wav/.mp3 for audio, .txt for transcripts)
- Ensure filenames match exactly
- Verify file size limits

### Performance Tips

- **Enable GPU**: Runtime → Change runtime type → Hardware accelerator → GPU
- **Use text splitting**: For inputs longer than 200 characters
- **Optimize parameters**: Lower temperature for consistency, higher CFG for quality
- **Batch processing**: Generate multiple short clips instead of one long one

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 8GB (12GB recommended)
- **Disk**: 4GB free space
- **Internet**: Stable connection for model download

### Recommended Setup
- **Runtime**: Python 3.8+
- **Hardware**: GPU-enabled (T4/P100/V100)
- **Storage**: High-speed persistent disk

## 🔄 Updates and Changes

This Colab version includes several improvements over the original server:

### ✅ Enhancements
- **GPU Support**: Automatic hardware acceleration
- **Interactive UI**: Modern widget-based interface
- **File Management**: Integrated upload/download
- **Progress Tracking**: Real-time generation feedback
- **Error Handling**: Better error messages and recovery

### ✅ Optimizations
- **Memory Management**: Efficient model loading and cleanup
- **Caching**: Smart model and dependency caching
- **Parallel Processing**: Optimized for Colab's environment
- **Resource Monitoring**: GPU memory and usage tracking

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Make your changes
3. Test in Google Colab
4. Submit a pull request

## 📄 License

This project is based on the original Dia TTS Server and follows the same license terms.

## 🙏 Acknowledgments

- **Dia Model**: Original TTS model by ttj
- **FastAPI**: Web framework for the original server
- **Google Colab**: Platform for this adaptation
- **Community**: Contributors and users of the TTS technology

---

**Happy TTS generation! 🎵**
