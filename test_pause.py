#!/usr/bin/env python3
"""
Test script to verify pause insertion functionality.
Tests text with various pause markers and generates audio to verify pauses work.
"""

import logging
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import the engine components
from engine import load_model, generate_speech
from utils import save_audio_to_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pause_insertion():
    """Test pause insertion with various marker types."""

    test_cases = [
        # Test 1: Simple pause
        ("[S1] Hello (pause=0.5) world!", "simple_pause.wav"),

        # Test 2: Ellipsis pause
        ("[S1] This is a test... with ellipses!", "ellipsis_pause.wav"),

        # Test 3: Em-dash pause
        ("[S1] Dramatic pause—then continue", "emdash_pause.wav"),

        # Test 4: Multiple pauses
        ("[S1] Hello (pause=0.2) there (pause=0.8) friend!", "multiple_pauses.wav"),

        # Test 5: Mixed pause types
        ("[S1] Thinking... (pause=0.3) indeed—and yes!", "mixed_pauses.wav")
    ]

    # Load model first
    logger.info("Loading Dia TTS model...")
    if not load_model():
        logger.error("Failed to load model")
        return False

    logger.info("Model loaded successfully. Testing pause insertion...")

    for i, (text, filename) in enumerate(test_cases):
        logger.info(f"\n=== Test Case {i+1}: {filename} ===")
        logger.info(f"Text: {text}")

        try:
            # Generate speech
            result = generate_speech(
                text_to_process=text,
                voice_mode="single_s1",
                speed_factor=1.0,  # No speed adjustment to focus on pauses
                seed=42  # Consistent seed for testing
            )

            if result is None:
                logger.error(f"Generation failed for test case {i+1}")
                continue

            audio_array, sample_rate = result
            logger.info(f"Generated audio: {audio_array.shape}, sample rate: {sample_rate}")

            # Save to file for inspection
            output_path = f"outputs/{filename}"
            success = save_audio_to_file(audio_array, sample_rate, output_path)

            if success:
                logger.info(f"Successfully saved: {output_path}")
                logger.info(f"Audio duration: {len(audio_array) / sample_rate:.2f} seconds")
            else:
                logger.error(f"Failed to save: {output_path}")

        except Exception as e:
            logger.error(f"Error in test case {i+1}: {e}")
            continue

    logger.info("\n=== Test Summary ===")
    logger.info("All test cases completed. Check 'outputs/' directory for generated audio files.")
    logger.info("Listen to the files to verify that pauses are inserted correctly at the expected positions.")

    return True

if __name__ == "__main__":
    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)

    logger.info("Starting pause insertion tests...")
    success = test_pause_insertion()

    if success:
        logger.info("Pause insertion tests completed!")
    else:
        logger.error("Some tests failed!")
        sys.exit(1)
