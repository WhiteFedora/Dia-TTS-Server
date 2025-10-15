#!/usr/bin/env python3
# setup_colab.py
# Setup script for Dia TTS in Google Colab

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a shell command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def install_requirements():
    """Install Python requirements."""
    print("📦 Installing Python requirements...")

    # Core scientific computing
    if not run_command("pip install torch torchaudio numpy -q", "Installing core ML libraries"):
        return False

    # Audio processing
    if not run_command("pip install soundfile librosa pydub praat-parselmouth -q", "Installing audio libraries"):
        return False

    # Hugging Face ecosystem
    if not run_command("pip install huggingface_hub safetensors descript-audio-codec -q", "Installing HF libraries"):
        return False

    # Speech processing
    if not run_command("pip install openai-whisper -q", "Installing Whisper"):
        return False

    # Web and utilities
    if not run_command("pip install fastapi uvicorn python-multipart pyyaml tqdm -q", "Installing web utilities"):
        return False

    # Jupyter widgets
    if not run_command("pip install ipywidgets -q", "Installing Jupyter widgets"):
        return False

    return True

def create_directories():
    """Create necessary directories."""
    print("📁 Creating directories...")

    dirs = [
        "/content/dia_tts/models",
        "/content/dia_tts/reference_audio",
        "/content/dia_tts/voices",
        "/content/dia_tts/outputs"
    ]

    for dir_path in dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            print(f"  ✅ Created: {dir_path}")
        except Exception as e:
            print(f"  ❌ Failed to create {dir_path}: {e}")
            return False

    return True

def check_dia_package():
    """Check if Dia package is available."""
    try:
        import dia
        print("✅ Dia package already installed")
        return True
    except ImportError:
        print("⚠️  Dia package not found")
        print("   You may need to install it separately:")
        print("   !pip install git+https://github.com/your-repo/dia.git")
        return False

def verify_imports():
    """Verify that all modules can be imported."""
    print("🔍 Verifying imports...")

    modules_to_test = [
        'colab_config',
        'colab_files',
        'engine_colab',
        'colab_ui'
    ]

    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            return False

    return True

def main():
    """Main setup function."""
    print("🚀 Setting up Dia TTS for Google Colab")
    print("=" * 50)

    # Check if running in Colab
    in_colab = 'google.colab' in sys.modules or 'COLAB_GPU' in os.environ
    if in_colab:
        print("🔍 Detected Google Colab environment")
    else:
        print("🔍 Running in local environment")

    # Install requirements
    if not install_requirements():
        print("❌ Installation failed")
        return False

    # Create directories
    if not create_directories():
        print("❌ Directory creation failed")
        return False

    # Check Dia package
    check_dia_package()

    # Verify imports
    if not verify_imports():
        print("❌ Import verification failed")
        return False

    print("=" * 50)
    print("✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Open dia_tts_colab.ipynb")
    print("2. Run the installation cell")
    print("3. Load the TTS model")
    print("4. Start generating audio!")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
