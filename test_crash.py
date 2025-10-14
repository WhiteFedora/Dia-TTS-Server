#!/usr/bin/env python3
"""
Test script to reproduce the crashing text issue with enhanced logging.
"""

import logging
import sys
import time

# Configure logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Import after logging setup
from engine import generate_speech, load_model

def test_crashing_text():
    """Test the specific crashing text provided in the task."""

    # Sample text that causes the crash
    text = "[S1] (sighs) Hey, how's it going?"
    voice_mode = "single_s1"
    seed = 42

    logger.info("=" * 60)
    logger.info("TESTING CRASHING TEXT WITH ENHANCED LOGGING")
    logger.info("=" * 60)
    logger.info(f"Text to process: {repr(text)}")
    logger.info(f"Voice mode: {voice_mode}")
    logger.info(f"Seed: {seed}")
    logger.info("=" * 60)

    # Ensure model is loaded
    logger.info("Checking model load status...")
    if not load_model():
        logger.error("Failed to load model. Cannot proceed with test.")
        return False

    logger.info("Model loaded successfully. Starting generation...")

    start_time = time.time()

    try:
        # Call generate_speech with the exact parameters from the crash report
        result = generate_speech(
            text_to_process=text,
            voice_mode=voice_mode,
            seed=seed,
            cfg_scale=2.9,  # From the crash report "cfg =2.9"
            # Default other parameters
            temperature=1.3,
            top_p=0.95,
            speed_factor=0.94,
            split_text=False
            # Note: verbose parameter may not exist, so omit it
        )

        end_time = time.time()
        generation_time = end_time - start_time

        if result is not None:
            audio_array, sample_rate = result
            logger.info("=" * 60)
            logger.info("GENERATION SUCCESSFUL!")
            logger.info(f"Generation time: {generation_time:.2f}s")
            logger.info(f"Sample rate: {sample_rate}")
            logger.info(f"Audio shape: {audio_array.shape}")
            logger.info("=" * 60)
            return True
        else:
            logger.error("=" * 60)
            logger.error("GENERATION FAILED - Returned None")
            logger.error(f"Generation time: {generation_time:.2f}s")
            logger.error("=" * 60)
            return False

    except Exception as e:
        end_time = time.time()
        generation_time = end_time - start_time
        logger.error("=" * 60)
        logger.error(f"GENERATION CRASHED after {generation_time:.3f}s")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception message: {str(e)}")
        logger.error("Full traceback:")
        import traceback
        traceback.print_exc()
        logger.error("=" * 60)
        return False

if __name__ == "__main__":
    success = test_crashing_text()
    logger.info(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
