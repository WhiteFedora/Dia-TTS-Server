#!/usr/bin/env python3
"""
Example 2: Advanced Prosody and Emotion Control (Phase 2 Feature)

This example demonstrates how to use emotion, speaking styles, and
prosody parameters for more natural and expressive speech generation.

NEW in Phase 2: emotion, speaking_style, pitch_shift, energy_level
"""

import requests
import json
from pathlib import Path
from enum import Enum

# Server configuration
SERVER_URL = "http://localhost:8003"
TTS_ENDPOINT = f"{SERVER_URL}/tts"
OUTPUT_DIR = Path("generated_audio")
OUTPUT_DIR.mkdir(exist_ok=True)


class Emotion(str, Enum):
    """Available emotions."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEARFUL = "fearful"


class SpeakingStyle(str, Enum):
    """Available speaking styles."""
    NORMAL = "normal"
    FORMAL = "formal"
    CASUAL = "casual"
    WHISPER = "whisper"
    SHOUTING = "shouting"


def generate_with_emotion(
    text: str,
    emotion: Emotion,
    speaking_style: SpeakingStyle,
    pitch_shift: float = 0.0,
    energy_level: float = 1.0,
    output_filename: str = "output.wav"
) -> bool:
    """
    Generate speech with specific emotion and style.
    
    Args:
        text: Text to generate
        emotion: Emotion to apply
        speaking_style: Speaking style
        pitch_shift: Pitch adjustment in semitones (-12 to +12)
        energy_level: Energy multiplier (0.5 to 2.0)
        output_filename: Output file name
    
    Returns:
        True if successful
    """
    payload = {
        "text": text,
        "voice_mode": "single_s1",
        "output_format": "wav",
        "emotion": emotion.value,
        "speaking_style": speaking_style.value,
        "pitch_shift": pitch_shift,
        "energy_level": energy_level,
        "cfg_scale": 3.0,
        "temperature": 1.3,
        "top_p": 0.95,
        "speed_factor": 1.0,
    }
    
    try:
        print(f"Generating with emotion={emotion.value}, style={speaking_style.value}...")
        response = requests.post(TTS_ENDPOINT, json=payload, timeout=300)
        
        if response.status_code == 200:
            output_path = OUTPUT_DIR / output_filename
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✓ Saved to: {output_path}")
            return True
        else:
            print(f"✗ Error: HTTP {response.status_code}")
            print(f"  {response.text}")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def emotion_arc_dialogue() -> bool:
    """
    Generate a dialogue with emotion arc (emotional progression).
    
    The same sentence spoken with different emotions to show progression:
    happy -> sad -> angry
    """
    print("\nGenerating Emotion Arc Dialogue...")
    print("-" * 40)
    
    text_happy = "[S1] I just got promoted! This is the best day ever!"
    text_sad = "[S1] I just got promoted, but... my friend didn't make the cut."
    text_angry = "[S1] I got promoted, but they passed over someone more deserving!"
    
    success = True
    success &= generate_with_emotion(
        text_happy,
        Emotion.HAPPY,
        SpeakingStyle.NORMAL,
        pitch_shift=2.0,
        energy_level=1.3,
        output_filename="emotion_arc_happy.wav"
    )
    
    success &= generate_with_emotion(
        text_sad,
        Emotion.SAD,
        SpeakingStyle.NORMAL,
        pitch_shift=-2.0,
        energy_level=0.7,
        output_filename="emotion_arc_sad.wav"
    )
    
    success &= generate_with_emotion(
        text_angry,
        Emotion.ANGRY,
        SpeakingStyle.NORMAL,
        pitch_shift=1.0,
        energy_level=1.5,
        output_filename="emotion_arc_angry.wav"
    )
    
    return success


def speaking_styles_demo() -> bool:
    """Generate the same text in different speaking styles."""
    print("\nGenerating Speaking Styles Demo...")
    print("-" * 40)
    
    text = "The quick brown fox jumps over the lazy dog"
    success = True
    
    for style in SpeakingStyle:
        energy = 1.0
        pitch = 0.0
        
        if style == SpeakingStyle.WHISPER:
            energy = 0.5
            pitch = -2.0
        elif style == SpeakingStyle.SHOUTING:
            energy = 1.5
            pitch = 2.0
        elif style == SpeakingStyle.FORMAL:
            pitch = 1.0
        
        success &= generate_with_emotion(
            text,
            Emotion.NEUTRAL,
            style,
            pitch_shift=pitch,
            energy_level=energy,
            output_filename=f"style_{style.value}.wav"
        )
    
    return success


def character_voice_demo() -> bool:
    """Generate dialogue with different character voices/emotions."""
    print("\nGenerating Character Voice Demo...")
    print("-" * 40)
    
    dialogue = {
        "excited_student": {
            "text": "I got an A on my exam! I studied so hard!",
            "emotion": Emotion.HAPPY,
            "style": SpeakingStyle.CASUAL,
            "pitch_shift": 3.0,  # Higher pitched voice
            "energy": 1.4,
        },
        "tired_teacher": {
            "text": "Great work, everyone. Please pass your papers forward.",
            "emotion": Emotion.NEUTRAL,
            "style": SpeakingStyle.FORMAL,
            "pitch_shift": -2.0,  # Lower pitched voice
            "energy": 0.8,
        },
        "worried_parent": {
            "text": "How was school today? I hope everything went well.",
            "emotion": Emotion.FEARFUL,
            "style": SpeakingStyle.NORMAL,
            "pitch_shift": 1.0,
            "energy": 0.9,
        },
    }
    
    success = True
    for char_name, params in dialogue.items():
        success &= generate_with_emotion(
            params["text"],
            params["emotion"],
            params["style"],
            pitch_shift=params["pitch_shift"],
            energy_level=params["energy"],
            output_filename=f"character_{char_name}.wav"
        )
    
    return success


def main():
    """Run prosody and emotion examples."""
    print("=" * 60)
    print("Dia TTS - Advanced Prosody & Emotion Control Examples")
    print("=" * 60)
    print("\nNEW Features (Phase 2):")
    print("  • Emotion: neutral, happy, sad, angry, surprised, fearful")
    print("  • Speaking Styles: normal, formal, casual, whisper, shouting")
    print("  • Pitch Shift: -12 to +12 semitones")
    print("  • Energy Level: 0.5 to 2.0 multiplier")
    print()
    
    all_success = True
    
    # Run all demos
    all_success &= emotion_arc_dialogue()
    all_success &= speaking_styles_demo()
    all_success &= character_voice_demo()
    
    print("\n" + "=" * 60)
    if all_success:
        print("✓ All examples completed successfully!")
    else:
        print("✗ Some examples failed. Check server logs.")
    print("=" * 60)
    print("\nAdvanced Tips:")
    print("  • Emotion affects pitch, energy, and vocal tone")
    print("  • Combine emotion + style for unique characters")
    print("  • Use pitch_shift for age/gender variations")
    print("  • High energy = louder, more dynamic")
    print("  • Low energy = quieter, more subdued")


if __name__ == "__main__":
    main()
