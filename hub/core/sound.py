from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

import pygame


class SoundManager:
    """Small synth-based sound manager backed by pygame.mixer."""

    TONES = {
        "click": (420, 0.08),
        "success": (640, 0.16),
        "move": (520, 0.10),
        "lose": (220, 0.22),
        "score": (760, 0.10),
    }

    def __init__(self, cache_dir: Path, settings_provider) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.settings_provider = settings_provider
        self.enabled = False
        self.sounds = {}

        try:
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.enabled = True
            for name, (freq, duration) in self.TONES.items():
                tone_path = self._ensure_tone(name, freq, duration)
                self.sounds[name] = pygame.mixer.Sound(str(tone_path))
        except Exception:
            self.enabled = False

    def _ensure_tone(self, name: str, frequency: int, duration: float) -> Path:
        path = self.cache_dir / f"{name}.wav"
        if path.exists():
            return path

        sample_rate = 44100
        amplitude = 14000
        frames = int(sample_rate * duration)
        with wave.open(str(path), "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for frame_index in range(frames):
                envelope = max(0.0, 1.0 - (frame_index / frames) * 1.4)
                sample = amplitude * envelope * math.sin(2 * math.pi * frequency * (frame_index / sample_rate))
                wav_file.writeframes(struct.pack("<h", int(sample)))
        return path

    def play(self, name: str) -> None:
        settings = self.settings_provider()
        if not (self.enabled and settings.get("sound_enabled", True)):
            return
        sound = self.sounds.get(name)
        if sound is None:
            return
        sound.set_volume(float(settings.get("volume", 60)) / 100.0)
        sound.play()
