#!/usr/bin/env python3
"""
Example 1: Simple Multi-Speaker Dialogue Generation

This example demonstrates how to generate natural-sounding dialogue
between two speakers using the Dia TTS Server.
"""

import requests
import json
from pathlib import Path

# Server configuration
SERVER_URL = "http://localhost:8003"
TTS_ENDPOINT = f"{SERVER_URL}/tts"
OUTPUT_DIR = Path("generated_audio")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_dialogue(dialogue_text: str, output_filename: str) -> bool:
    """
    Generate dialogue audio from text with [S1] and [S2] speaker tags.
    
    Args:
        dialogue_text: Text with speaker tags ([S1] and [S2])
        output_filename: Filename to save audio to
    
    Returns:
        True if successful, False otherwise
    """
    payload = {
        "text": dialogue_text,
        "voice_mode": "dialogue",
        "output_format": "wav",
        "cfg_scale": 3.0,
        "temperature": 1.3,
        "top_p": 0.95,
        "speed_factor": 1.0,
        "split_text": True,
        "chunk_size": 300,
        # Note: emotion/speaking_style are NEW in Phase 2
    }
    
    try:
        print(f"Generating dialogue...")
        response = requests.post(TTS_ENDPOINT, json=payload, timeout=300)
        
        if response.status_code == 200:
            output_path = OUTPUT_DIR / output_filename
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✓ Successfully saved to: {output_path}")
            print(f"  File size: {len(response.content) / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"✗ Error: HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("✗ Request timed out (model still loading?)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"✗ Could not connect to server at {SERVER_URL}")
        print("  Make sure the server is running: python server.py")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False


def main():
    """Run dialogue generation examples."""
    print("=" * 60)
    print("Dia TTS - Simple Dialogue Generation Example")
    print("=" * 60)
    
    # Example 1: Simple conversation
    dialogue_1 = """[S1] Hello! How are you doing today?
[S2] I'm doing great, thanks for asking! The weather is beautiful.
[S1] Indeed it is. Would you like to go for a walk?
[S2] That sounds wonderful! Let's go to the park."""
    
    generate_dialogue(dialogue_1, "example_simple_dialogue.wav")
    
    # Example 2: Longer conversation
    dialogue_2 = """[S1] Good morning! I have great news!
[S2] Tell me, tell me! What is it?
[S1] We got the project! The whole team worked so hard.
[S2] That's fantastic! Congratulations! We should celebrate!
[S1] Absolutely. Let's grab lunch at that new restaurant.
[S2] Perfect! I've been wanting to try it. Let's go now!"""
    
    generate_dialogue(dialogue_2, "example_longer_dialogue.wav")
    
    # Example 3: Dramatic conversation
    dialogue_3 = """[S1] I need to tell you something important.
[S2] What is it? You're scaring me.
[S1] Don't worry. It's actually good news. I've been offered a promotion!
[S2] That's incredible! When do you start?
[S1] Next month. I'll be leading the new project team.
[S2] I'm so proud of you! This is what you've been working for!"""
    
    generate_dialogue(dialogue_3, "example_dramatic_dialogue.wav")
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nTips for best results:")
    print("  • Keep lines short and natural")
    print("  • Use proper punctuation")
    print("  • Vary line length for naturalness")
    print("  • Tag with [S1] and [S2] for proper speaker tracking")
    print("\nFor advanced features (emotion, styles), see example_prosody.py")


if __name__ == "__main__":
    main()
