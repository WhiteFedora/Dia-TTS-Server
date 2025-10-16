# prosody_manager.py
# Prosody, emotion, and speaking style management for multi-speaker generation

import logging
from dataclasses import dataclass
from typing import Optional, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class Emotion(str, Enum):
    """Supported emotion types."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEARFUL = "fearful"


class SpeakingStyle(str, Enum):
    """Supported speaking styles."""
    NORMAL = "normal"
    FORMAL = "formal"
    CASUAL = "casual"
    WHISPER = "whisper"
    SHOUTING = "shouting"


@dataclass
class ProsodyProfile:
    """
    Prosody parameters for a speaker or turn.
    
    Attributes:
        rate: Speaking rate multiplier (0.5 = half speed, 1.5 = 1.5x speed).
        pitch: Pitch shift in semitones (-12 to +12).
        energy: Energy/volume multiplier (0.0 to 2.0).
        emotion: Emotion type.
        style: Speaking style.
        pause_ms: Pause duration before speaking in milliseconds.
    """
    rate: float = 1.0
    pitch: float = 0.0  # semitones
    energy: float = 1.0
    emotion: Emotion = Emotion.NEUTRAL
    style: SpeakingStyle = SpeakingStyle.NORMAL
    pause_ms: int = 0
    
    def to_prefix(self) -> str:
        """Convert prosody profile to text prefix for model input."""
        parts = []
        
        if self.emotion != Emotion.NEUTRAL:
            parts.append(f"[{self.emotion.value}]")
        
        if self.style != SpeakingStyle.NORMAL:
            parts.append(f"[{self.style.value}]")
        
        if self.rate != 1.0:
            parts.append(f"[rate={self.rate:.2f}]")
        
        if self.pitch != 0:
            parts.append(f"[pitch={self.pitch:+.1f}]")
        
        if self.energy != 1.0:
            parts.append(f"[energy={self.energy:.2f}]")
        
        return " ".join(parts) + " " if parts else ""
    
    @staticmethod
    def from_dict(data: Dict) -> 'ProsodyProfile':
        """Create profile from dictionary."""
        return ProsodyProfile(
            rate=float(data.get('rate', 1.0)),
            pitch=float(data.get('pitch', 0.0)),
            energy=float(data.get('energy', 1.0)),
            emotion=Emotion(data.get('emotion', 'neutral')),
            style=SpeakingStyle(data.get('style', 'normal')),
            pause_ms=int(data.get('pause_ms', 0))
        )


class ProsodyPreset:
    """Predefined prosody presets for common use cases."""
    
    PRESETS = {
        'enthusiastic': ProsodyProfile(
            rate=1.1,
            pitch=+2,
            energy=1.3,
            emotion=Emotion.HAPPY,
            style=SpeakingStyle.NORMAL
        ),
        'calm': ProsodyProfile(
            rate=0.9,
            pitch=-1,
            energy=0.8,
            emotion=Emotion.NEUTRAL,
            style=SpeakingStyle.FORMAL
        ),
        'energetic': ProsodyProfile(
            rate=1.2,
            pitch=+1,
            energy=1.4,
            emotion=Emotion.HAPPY,
            style=SpeakingStyle.CASUAL
        ),
        'sad': ProsodyProfile(
            rate=0.85,
            pitch=-2,
            energy=0.7,
            emotion=Emotion.SAD,
            style=SpeakingStyle.NORMAL
        ),
        'angry': ProsodyProfile(
            rate=1.15,
            pitch=+3,
            energy=1.5,
            emotion=Emotion.ANGRY,
            style=SpeakingStyle.NORMAL
        ),
        'whisper': ProsodyProfile(
            rate=0.95,
            pitch=0,
            energy=0.5,
            emotion=Emotion.NEUTRAL,
            style=SpeakingStyle.WHISPER
        ),
    }
    
    @classmethod
    def get(cls, name: str) -> Optional[ProsodyProfile]:
        """Get preset by name."""
        return cls.PRESETS.get(name.lower())
    
    @classmethod
    def list(cls) -> List[str]:
        """List available preset names."""
        return list(cls.PRESETS.keys())


@dataclass
class SpeakerProfile:
    """
    Complete speaker profile including voice characteristics and default prosody.
    
    Attributes:
        speaker_id: Unique identifier (e.g., 'S1', 'S2', 'narrator').
        voice_filename: Reference audio filename for cloning (optional).
        transcript: Reference transcript for cloning (optional).
        default_prosody: Default prosody profile for this speaker.
        name: Display name for this speaker.
    """
    speaker_id: str
    default_prosody: ProsodyProfile
    voice_filename: Optional[str] = None
    transcript: Optional[str] = None
    name: Optional[str] = None
    
    @staticmethod
    def from_dict(data: Dict) -> 'SpeakerProfile':
        """Create profile from dictionary."""
        return SpeakerProfile(
            speaker_id=data['speaker_id'],
            voice_filename=data.get('voice_filename'),
            transcript=data.get('transcript'),
            default_prosody=ProsodyProfile.from_dict(data.get('prosody', {})),
            name=data.get('name')
        )


class ProsodyManager:
    """Manager for prosody and emotion in multi-speaker scenarios."""
    
    def __init__(self):
        """Initialize prosody manager."""
        self.speaker_profiles: Dict[str, SpeakerProfile] = {}
        self.current_emotion_arc: List[Emotion] = []
    
    def register_speaker(self, profile: SpeakerProfile) -> None:
        """Register a speaker profile."""
        self.speaker_profiles[profile.speaker_id] = profile
        logger.info(f"Registered speaker profile: {profile.speaker_id}")
    
    def get_speaker(self, speaker_id: str) -> Optional[SpeakerProfile]:
        """Get speaker profile by ID."""
        return self.speaker_profiles.get(speaker_id)
    
    def apply_emotion_arc(self, emotions: List[Emotion]) -> None:
        """
        Set an emotion arc for the dialogue.
        
        Args:
            emotions: List of emotions to apply throughout turns.
        """
        self.current_emotion_arc = emotions
        logger.info(f"Emotion arc set: {[e.value for e in emotions]}")
    
    def get_turn_prosody(self, turn_index: int, override_prosody: Optional[ProsodyProfile] = None) -> ProsodyProfile:
        """
        Get prosody for a specific turn, considering emotion arc.
        
        Args:
            turn_index: Index in the turn sequence.
            override_prosody: Optional prosody profile to use as base.
        
        Returns:
            ProsodyProfile for this turn.
        """
        prosody = override_prosody or ProsodyProfile()
        
        # Apply emotion from arc if available
        if self.current_emotion_arc and turn_index < len(self.current_emotion_arc):
            prosody.emotion = self.current_emotion_arc[turn_index]
        
        return prosody
    
    def build_turn_text(self, speaker_id: str, text: str, prosody: Optional[ProsodyProfile] = None) -> str:
        """
        Build complete turn text with speaker tag and prosody.
        
        Args:
            speaker_id: Speaker identifier.
            text: Text to speak.
            prosody: Optional prosody profile to apply.
        
        Returns:
            Formatted turn text ready for model input.
        """
        if not speaker_id.startswith('['):
            speaker_tag = f"[{speaker_id}]"
        else:
            speaker_tag = speaker_id
        
        profile = self.get_speaker(speaker_id)
        prosody_profile = prosody or (profile.default_prosody if profile else ProsodyProfile())
        prosody_prefix = prosody_profile.to_prefix()
        
        return f"{speaker_tag} {prosody_prefix}{text}"


def format_prosody_for_api(prosody: ProsodyProfile) -> Dict:
    """
    Format prosody profile for API/JSON serialization.
    
    Args:
        prosody: ProsodyProfile object.
    
    Returns:
        Dictionary representation.
    """
    return {
        'rate': prosody.rate,
        'pitch': prosody.pitch,
        'energy': prosody.energy,
        'emotion': prosody.emotion.value,
        'style': prosody.style.value,
        'pause_ms': prosody.pause_ms
    }
