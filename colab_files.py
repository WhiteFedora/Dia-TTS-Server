# colab_files.py
# File management utilities for Google Colab environment

import os
import shutil
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class ColabFileManager:
    """Manages files and directories in Google Colab environment."""

    def __init__(self, base_path: str = "/content/dia_tts"):
        self.base_path = Path(base_path)
        self._ensure_base_directories()

    def _ensure_base_directories(self):
        """Create base directories if they don't exist."""
        directories = [
            self.base_path / "models",
            self.base_path / "reference_audio",
            self.base_path / "voices",
            self.base_path / "outputs",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_reference_files(self) -> List[str]:
        """Get list of reference audio files."""
        ref_path = self.base_path / "reference_audio"
        files = []

        if ref_path.exists():
            for file_path in ref_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in ['.wav', '.mp3']:
                    files.append(file_path.name)

        return sorted(files)

    def get_predefined_voices(self) -> List[Dict[str, str]]:
        """Get list of predefined voice files."""
        voices_path = self.base_path / "voices"
        voices = []

        if voices_path.exists():
            for file_path in voices_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() == '.wav':
                    base_name = file_path.stem
                    display_name = base_name.replace('_', '-')
                    voices.append({
                        'display_name': display_name,
                        'filename': file_path.name
                    })

        return sorted(voices, key=lambda x: x['display_name'])

    def save_uploaded_file(self, file_data, filename: str, subfolder: str = "reference_audio") -> str:
        """Save uploaded file to appropriate directory."""
        target_dir = self.base_path / subfolder
        target_path = target_dir / filename

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        with open(target_path, 'wb') as f:
            f.write(file_data)

        logger.info(f"Saved uploaded file: {target_path}")
        return str(target_path)

    def save_generated_audio(self, audio_data: bytes, filename: str) -> str:
        """Save generated audio file."""
        output_path = self.base_path / "outputs" / filename

        with open(output_path, 'wb') as f:
            f.write(audio_data)

        logger.info(f"Saved generated audio: {output_path}")
        return str(output_path)

    def get_file_path(self, filename: str, subfolder: str = "reference_audio") -> Optional[str]:
        """Get full path for a file in a subdirectory."""
        file_path = self.base_path / subfolder / filename
        return str(file_path) if file_path.exists() else None

    def list_directory(self, subfolder: str) -> List[str]:
        """List files in a subdirectory."""
        dir_path = self.base_path / subfolder

        if not dir_path.exists():
            return []

        return [f.name for f in dir_path.iterdir() if f.is_file()]

    def cleanup_old_files(self, subfolder: str, keep_recent: int = 10):
        """Clean up old files in a subdirectory, keeping only the most recent ones."""
        dir_path = self.base_path / subfolder

        if not dir_path.exists():
            return

        files = []
        for file_path in dir_path.iterdir():
            if file_path.is_file():
                files.append((file_path, file_path.stat().st_mtime))

        # Sort by modification time, newest first
        files.sort(key=lambda x: x[1], reverse=True)

        # Remove old files
        for file_path, _ in files[keep_recent:]:
            try:
                file_path.unlink()
                logger.info(f"Removed old file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove old file {file_path}: {e}")


# Global file manager instance
file_manager = ColabFileManager()


def get_reference_files() -> List[str]:
    """Get list of reference audio files."""
    return file_manager.get_reference_files()


def get_predefined_voices() -> List[Dict[str, str]]:
    """Get list of predefined voice files."""
    return file_manager.get_predefined_voices()


def save_uploaded_file(file_data, filename: str, subfolder: str = "reference_audio") -> str:
    """Save uploaded file to appropriate directory."""
    return file_manager.save_uploaded_file(file_data, filename, subfolder)


def save_generated_audio(audio_data: bytes, filename: str) -> str:
    """Save generated audio file."""
    return file_manager.save_generated_audio(audio_data, filename)


def get_file_path(filename: str, subfolder: str = "reference_audio") -> Optional[str]:
    """Get full path for a file in a subdirectory."""
    return file_manager.get_file_path(filename, subfolder)


def list_directory(subfolder: str) -> List[str]:
    """List files in a subdirectory."""
    return file_manager.list_directory(subfolder)
