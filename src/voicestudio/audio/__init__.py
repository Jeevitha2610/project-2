"""
VoiceStudio Audio Processing & Quality Validation Package.
"""

from voicestudio.audio.processor import AudioProcessor, PreprocessedAudio
from voicestudio.audio.validator import (
    AudioValidator,
    AudioValidationError,
    InvalidAudioFormatError,
    AudioTooShortError,
    AudioTooLongError,
    AudioClippingError,
    AudioSilentError,
    ExcessiveNoiseError,
    AudioFormatResult,
    QualityValidationResult,
)

__all__ = [
    "AudioProcessor",
    "PreprocessedAudio",
    "AudioValidator",
    "AudioValidationError",
    "InvalidAudioFormatError",
    "AudioTooShortError",
    "AudioTooLongError",
    "AudioClippingError",
    "AudioSilentError",
    "ExcessiveNoiseError",
    "AudioFormatResult",
    "QualityValidationResult",
]
