# engine_colab.py
# Core Dia TTS engine adapted for Google Colab

import logging
import time
import os
import torch
import torchaudio
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from huggingface_hub import hf_hub_download
from tqdm import tqdm

# Import Dia model components
try:
    from dia.model import Dia, ComputeDtype, DEFAULT_SAMPLE_RATE
    from dia.config import DiaConfig
except ImportError as e:
    logging.critical(f"Failed to import Dia model components: {e}")
    Dia = None
    DiaConfig = None
    ComputeDtype = None
    DEFAULT_SAMPLE_RATE = 44100

# Import Colab-specific modules
from colab_config import (
    get_device, get_compute_dtype, get_model_repo_id,
    get_model_cache_path, get_reference_audio_path,
    get_model_config_filename, get_model_weights_filename,
    get_whisper_model_name, get_gen_default_speed_factor,
    get_gen_default_cfg_scale, get_gen_default_temperature,
    get_gen_default_top_p, get_gen_default_cfg_filter_top_k,
    get_gen_default_seed, get_gen_default_split_text,
    get_gen_default_chunk_size
)

# Import utilities (adapted for Colab)
from utils import (
    chunk_text_by_sentences, PerformanceMonitor,
    trim_lead_trail_silence, fix_internal_silence,
    remove_long_unvoiced_segments, _generate_transcript_with_whisper,
    time_stretch_audio, format_prosody_prefix, insert_pauses_into_audio,
    parse_scripting_markers
)

logger = logging.getLogger(__name__)

# Global variables
dia_model: Optional[Dia] = None
model_device: Optional[str] = None
MODEL_LOADED = False
EXPECTED_SAMPLE_RATE = DEFAULT_SAMPLE_RATE


def load_model() -> bool:
    """Load the Dia TTS model for Colab environment."""
    global dia_model, model_device, MODEL_LOADED, EXPECTED_SAMPLE_RATE

    if MODEL_LOADED and dia_model is not None:
        logger.info("Dia model already loaded.")
        return True

    # Get configuration
    repo_id = get_model_repo_id()
    config_filename = get_model_config_filename()
    weights_filename = get_model_weights_filename()
    cache_path = get_model_cache_path()
    device = get_device()
    compute_dtype = get_compute_dtype()

    model_device = device

    logger.info("Loading Dia model for Colab:")
    logger.info(f"  Repo ID: {repo_id}")
    logger.info(f"  Config File: {config_filename}")
    logger.info(f"  Weights File: {weights_filename}")
    logger.info(f"  Cache Directory: {cache_path}")
    logger.info(f"  Target Device: {device}")
    logger.info(f"  Compute Dtype: {compute_dtype}")

    try:
        start_time = time.time()

        # Download model files
        logger.info("Downloading model configuration...")
        local_config_path = hf_hub_download(
            repo_id=repo_id,
            filename=config_filename,
            cache_dir=cache_path
        )

        logger.info("Downloading model weights...")
        local_weights_path = hf_hub_download(
            repo_id=repo_id,
            filename=weights_filename,
            cache_dir=cache_path
        )

        # Load configuration
        config = DiaConfig.load(local_config_path)
        if config is None:
            raise FileNotFoundError(f"Failed to load config from {local_config_path}")

        # Initialize model
        logger.info("Initializing Dia model...")
        dia_instance = Dia(config, compute_dtype=compute_dtype, device=device)

        # Load weights
        logger.info("Loading model weights...")
        map_location = torch.device("cpu")  # Load to CPU first

        if local_weights_path.endswith(".safetensors"):
            from safetensors.torch import load_file
            state_dict = load_file(local_weights_path, device=str(map_location))
        elif local_weights_path.endswith(".pth"):
            state_dict = torch.load(local_weights_path, map_location=map_location)
        else:
            raise ValueError(f"Unsupported weights file format: {weights_filename}")

        # Apply weights
        dia_instance.model.load_state_dict(state_dict)

        # Move to target device
        dia_instance.model.to(device)
        dia_instance.model.eval()

        # Load DAC model
        logger.info("Loading DAC model...")
        dia_instance._load_dac_model()

        # Update global variables
        dia_model = dia_instance
        EXPECTED_SAMPLE_RATE = DEFAULT_SAMPLE_RATE
        MODEL_LOADED = True

        end_time = time.time()
        logger.info(f"Dia model loaded successfully in {end_time - start_time:.2f} seconds.")

        # Log GPU memory if using CUDA
        if device == "cuda":
            if torch.cuda.is_available():
                memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"GPU Memory: {memory_gb:.1f}GB")

        return True

    except Exception as e:
        logger.error(f"Error loading Dia model: {e}", exc_info=True)
        MODEL_LOADED = False
        return False


def generate_speech(
    text_to_process: str,
    voice_mode: str = "single_s1",
    clone_reference_filename: Optional[str] = None,
    transcript: Optional[str] = None,
    speed_factor: float = 1.0,
    cfg_scale: float = 3.0,
    temperature: float = 1.3,
    top_p: float = 0.95,
    cfg_filter_top_k: int = 35,
    seed: Optional[int] = None,
    split_text: bool = True,
    chunk_size: int = 120,
    enable_silence_trimming: bool = True,
    enable_internal_silence_fix: bool = True,
    enable_unvoiced_removal: bool = True,
) -> Optional[Tuple[np.ndarray, int]]:
    """Generate speech using the loaded Dia model."""

    if not MODEL_LOADED or dia_model is None:
        logger.error("Dia model is not loaded. Cannot generate speech.")
        return None

    monitor = PerformanceMonitor()
    monitor.record("Generation started")

    # Parse scripting markers
    cleaned_text, markers = parse_scripting_markers(text_to_process)
    logger.info(f"Parsed {len(markers)} scripting markers")

    # Handle text splitting
    if split_text and len(cleaned_text) < chunk_size * 2:
        split_text = False

    text_chunks = []
    if split_text:
        text_chunks = chunk_text_by_sentences(cleaned_text, chunk_size)
        logger.info(f"Split text into {len(text_chunks)} chunks")
    else:
        if cleaned_text.strip():
            text_chunks.append(cleaned_text)

    if not text_chunks:
        logger.warning("No text chunks to process")
        return None

    # Set seed
    if seed is None:
        seed = get_gen_default_seed()

    if seed >= 0:
        torch.manual_seed(seed)
        if model_device == "cuda":
            torch.cuda.manual_seed_all(seed)

    # Prepare for cloning if needed
    reference_transcript_text = None
    validated_clone_audio_path = None

    if voice_mode == "clone":
        if not clone_reference_filename:
            logger.error("Clone mode selected but no reference filename provided")
            return None

        ref_path = get_reference_audio_path()
        if os.path.isfile(clone_reference_filename):
            validated_clone_audio_path = clone_reference_filename
        else:
            # Look for file in reference audio directory
            potential_path = os.path.join(ref_path, clone_reference_filename)
            if os.path.isfile(potential_path):
                validated_clone_audio_path = potential_path
            else:
                logger.error(f"Reference file not found: {potential_path}")
                return None

        # Get transcript for cloning
        _, ref_transcript, prep_error = _prepare_cloning_inputs(
            clone_reference_filename=validated_clone_audio_path,
            reference_audio_base_path=ref_path,
            max_ref_duration_sec=20.0,
            whisper_model_name=get_whisper_model_name(),
            whisper_cache_path=get_model_cache_path(),
            transcript=transcript,
        )

        if prep_error:
            logger.error(f"Cloning preparation failed: {prep_error}")
            return None

        reference_transcript_text = ref_transcript

    monitor.record("Parameters processed")

    # Generate audio for each chunk
    all_audio_arrays = []

    for i, chunk in enumerate(text_chunks):
        logger.info(f"Processing chunk {i+1}/{len(text_chunks)}")

        # Prepare input text
        if voice_mode == "clone" and reference_transcript_text:
            text_input = reference_transcript_text + " " + chunk
        else:
            text_input = chunk

        try:
            # Generate audio for this chunk
            chunk_output = dia_model.generate(
                text=text_input,
                audio_prompt=validated_clone_audio_path,
                cfg_scale=cfg_scale,
                temperature=temperature,
                top_p=top_p,
                cfg_filter_top_k=cfg_filter_top_k,
                use_torch_compile=False,
                verbose=True,
                text_to_generate_size=len(chunk),
                seed=seed,
            )

            if chunk_output is not None and chunk_output.size > 0:
                all_audio_arrays.append(chunk_output)
                logger.info(f"Chunk {i+1} generated successfully")
            else:
                logger.warning(f"Chunk {i+1} generated no audio")

        except Exception as e:
            logger.error(f"Error generating chunk {i+1}: {e}")
            continue

    if not all_audio_arrays:
        logger.error("No audio generated from any chunk")
        return None

    # Concatenate all chunks
    final_audio_np = np.concatenate(all_audio_arrays)
    monitor.record("Audio concatenated")

    # Apply pause insertion if markers exist
    if markers:
        final_audio_np = insert_pauses_into_audio(final_audio_np, markers, EXPECTED_SAMPLE_RATE)
        monitor.record("Pauses inserted")

    # Apply speed factor
    if speed_factor != 1.0:
        logger.info(f"Applying speed factor: {speed_factor}")
        original_len = len(final_audio_np)
        speed_factor = max(0.5, min(speed_factor, 2.0))
        target_len = int(original_len / speed_factor)

        if target_len > 0 and target_len != original_len:
            x_original = np.linspace(0, 1, original_len)
            x_resampled = np.linspace(0, 1, target_len)
            final_audio_np = np.interp(x_resampled, x_original, final_audio_np).astype(np.float32)
            logger.info(f"Audio resampled: {original_len} -> {len(final_audio_np)} samples")

    # Apply post-processing
    if enable_silence_trimming:
        final_audio_np = trim_lead_trail_silence(final_audio_np, sample_rate=EXPECTED_SAMPLE_RATE)

    if enable_internal_silence_fix:
        final_audio_np = fix_internal_silence(final_audio_np, sample_rate=EXPECTED_SAMPLE_RATE)

    # Ensure correct data type
    if final_audio_np.dtype != np.float32:
        final_audio_np = final_audio_np.astype(np.float32)

    logger.info(f"Generation complete. Final audio shape: {final_audio_np.shape}")
    monitor.record("Generation complete")

    return final_audio_np, EXPECTED_SAMPLE_RATE


def _prepare_cloning_inputs(
    clone_reference_filename: str,
    reference_audio_base_path: str,
    max_ref_duration_sec: float,
    whisper_model_name: str,
    whisper_cache_path: str,
    transcript: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Prepare inputs for voice cloning."""

    reference_audio_path = os.path.join(reference_audio_base_path, clone_reference_filename)
    if not os.path.isfile(reference_audio_path):
        return None, None, f"Reference audio file not found: {reference_audio_path}"

    try:
        # Load and process audio
        audio_tensor, sr = torchaudio.load(reference_audio_path)

        if sr != EXPECTED_SAMPLE_RATE:
            audio_tensor = torchaudio.functional.resample(audio_tensor, sr, EXPECTED_SAMPLE_RATE)

        if audio_tensor.shape[0] > 1:
            audio_tensor = torch.mean(audio_tensor, dim=0, keepdim=True)

        # Truncate if necessary
        num_samples = audio_tensor.shape[1]
        duration_sec = num_samples / EXPECTED_SAMPLE_RATE

        if duration_sec > max_ref_duration_sec:
            target_samples = int(max_ref_duration_sec * EXPECTED_SAMPLE_RATE)
            audio_tensor = audio_tensor[:, :target_samples]

        processed_audio_np = audio_tensor.squeeze(0).numpy().astype(np.float32)

    except Exception as e:
        return None, None, f"Failed to load audio: {e}"

    # Get transcript
    transcript_text = None

    if transcript is not None:
        transcript_text = transcript.strip()
        if not transcript_text.startswith(("[S1]", "[S2]")):
            transcript_text = "[S1] " + transcript_text
    else:
        # Try to load transcript file
        base_name, _ = os.path.splitext(clone_reference_filename)
        transcript_filepath = os.path.join(reference_audio_base_path, base_name + ".txt")

        if os.path.isfile(transcript_filepath):
            try:
                with open(transcript_filepath, "r", encoding="utf-8") as f:
                    transcript_text = f.read().strip()
                if not transcript_text.startswith(("[S1]", "[S2]")):
                    transcript_text = "[S1] " + transcript_text
            except Exception:
                transcript_text = None

        # Try Whisper if no transcript file
        if transcript_text is None:
            generated_transcript = _generate_transcript_with_whisper(
                processed_audio_np, whisper_model_name, whisper_cache_path
            )
            if generated_transcript:
                transcript_text = "[S1] " + generated_transcript.strip()

    if transcript_text is None:
        return None, None, "Failed to obtain transcript"

    return None, transcript_text, None


def get_model_status() -> Dict[str, Any]:
    """Get current model status."""
    return {
        "loaded": MODEL_LOADED,
        "device": model_device,
        "sample_rate": EXPECTED_SAMPLE_RATE,
        "model_type": "Dia TTS"
    }
