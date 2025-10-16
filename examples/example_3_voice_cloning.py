#!/usr/bin/env python3
"""
Example 3: Voice Cloning

This example shows how to clone a speaker's voice using a reference
audio file and optional transcript.
"""

import requests
from pathlib import Path

# Server configuration
SERVER_URL = "http://localhost:8003"
TTS_ENDPOINT = f"{SERVER_URL}/tts"
OUTPUT_DIR = Path("generated_audio")
OUTPUT_DIR.mkdir(exist_ok=True)


def clone_voice(
    text_to_generate: str,
    reference_filename: str,
    transcript: str = None,  # type: ignore
    output_filename: str = "cloned_voice.wav"
) -> bool:
    """
    Clone a speaker's voice using a reference audio file.
    
    Args:
        text_to_generate: Text to generate in the cloned voice
        reference_filename: Filename in reference_audio/ directory
        transcript: Optional transcript of the reference audio
        output_filename: Where to save the output
    
    Returns:
        True if successful
    """
    payload = {
        "text": text_to_generate,
        "voice_mode": "clone",
        "clone_reference_filename": reference_filename,
        "transcript": transcript,  # Optional: if not provided, Whisper will transcribe
        "output_format": "wav",
        "cfg_scale": 3.0,
        "temperature": 1.3,
        "top_p": 0.95,
        "speed_factor": 1.0,
    }
    
    try:
        print(f"Cloning voice from: {reference_filename}")
        if transcript:
            print(f"Using provided transcript: {transcript[:50]}...")
        else:
            print("Transcript will be auto-generated with Whisper...")
        
        response = requests.post(TTS_ENDPOINT, json=payload, timeout=600)
        
        if response.status_code == 200:
            output_path = OUTPUT_DIR / output_filename
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✓ Successfully cloned voice")
            print(f"  Saved to: {output_path}")
            print(f"  File size: {len(response.content) / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"✗ Error: HTTP {response.status_code}")
            print(f"  {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("✗ Request timed out (cloning takes longer)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to server at {SERVER_URL}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run voice cloning examples."""
    print("=" * 60)
    print("Dia TTS - Voice Cloning Example")
    print("=" * 60)
    print()
    
    # Example texts to generate
    examples = [
        {
            "name": "Simple Sentence",
            "text": "The quick brown fox jumps over the lazy dog.",
            "reference": "Oliver_Luna.txt",  # Make sure this file exists!
        },
        {
            "name": "Longer Text",
            "text": "Today is a wonderful day. The weather is beautiful, "
                   "and I'm feeling energetic and ready to accomplish great things.",
            "reference": "Oliver_Luna.txt",
        },
        {
            "name": "With Transcript Override",
            "text": "This is a completely new sentence in the same voice.",
            "reference": "Oliver_Luna.txt",
            "transcript": "the original recording said something different",
        },
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}: {example['name']}")
        print("-" * 40)
        
        output_name = f"cloned_{i:02d}_{example['name'].lower().replace(' ', '_')}.wav"
        transcript = example.get("transcript")
        
        success = clone_voice(
            text_to_generate=example["text"],
            reference_filename=example["reference"],
            transcript=transcript,
            output_filename=output_name
        )
        
        if not success and i == 1:
            print("\n⚠ First example failed. Possible issues:")
            print("  1. Reference file not found in reference_audio/ directory")
            print("  2. Server not running (start with: python server.py)")
            print("  3. Whisper model not downloaded yet (takes time on first run)")
            break
        
        print()
    
    print("=" * 60)
    print("Voice Cloning Examples Complete")
    print("=" * 60)
    print("\nTips for Voice Cloning:")
    print("  • Reference audio should be 10-20 seconds")
    print("  • Clear, clean audio works best")
    print("  • Provide transcript if available for better results")
    print("  • First run will be slower (Whisper model downloads)")
    print("  • Cloned voice will match the reference closely")
    print("\nReference Audio Setup:")
    print("  1. Place audio files (.wav, .mp3) in: reference_audio/")
    print("  2. Optionally add .txt files with transcripts")
    print("  3. Transcripts will auto-generate with Whisper if missing")


if __name__ == "__main__":
    main()
