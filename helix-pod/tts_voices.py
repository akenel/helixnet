#!/usr/bin/env python3
"""
TTS Voices for Johnny's Story Teller
=====================================
Grandma (female) and Grandpa (male) voices for each language.
Uses edge-tts (Microsoft Edge TTS) - FREE, no API key needed.

Usage:
    from tts_voices import generate_audio
    generate_audio("Das ist ein Held", lang="de", voice="grandma", output="story.mp3")
"""

import asyncio
import edge_tts
from pathlib import Path

# Voice mapping: lang -> (grandma_voice, grandpa_voice)
VOICES = {
    "en": ("en-US-JennyNeural", "en-US-GuyNeural"),
    "de": ("de-DE-KatjaNeural", "de-DE-ConradNeural"),
    "fr": ("fr-FR-DeniseNeural", "fr-FR-HenriNeural"),
    "it": ("it-IT-ElsaNeural", "it-IT-DiegoNeural"),
    "es": ("es-ES-ElviraNeural", "es-ES-AlvaroNeural"),
    "hi": ("hi-IN-SwaraNeural", "hi-IN-MadhurNeural"),
    "th": ("th-TH-PremwadeeNeural", "th-TH-NiwatNeural"),
    "ar": ("ar-SA-ZariyahNeural", "ar-SA-HamedNeural"),
    "zh": ("zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural"),
    "ja": ("ja-JP-NanamiNeural", "ja-JP-KeitaNeural"),
    "ko": ("ko-KR-SunHiNeural", "ko-KR-InJoonNeural"),
    "pt": ("pt-BR-FranciscaNeural", "pt-BR-AntonioNeural"),
    "ru": ("ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"),
    "nl": ("nl-NL-ColetteNeural", "nl-NL-MaartenNeural"),
    "pl": ("pl-PL-ZofiaNeural", "pl-PL-MarekNeural"),
    "sv": ("sv-SE-SofieNeural", "sv-SE-MattiasNeural"),
    "tr": ("tr-TR-EmelNeural", "tr-TR-AhmetNeural"),
    "vi": ("vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"),
}

# Default fallback
DEFAULT_VOICE = ("en-US-JennyNeural", "en-US-GuyNeural")

# Slow, clear rate for kids
RATE = "-10%"  # Slightly slower than normal


async def _generate_audio_async(text: str, voice: str, output_path: str, rate: str = RATE):
    """Generate audio file using edge-tts (async)."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def generate_audio(text: str, lang: str = "en", voice_type: str = "grandma", output_path: str = None) -> str:
    """
    Generate audio from text.

    Args:
        text: The story text to speak
        lang: Language code (en, de, fr, it, etc.)
        voice_type: "grandma" (female) or "grandpa" (male)
        output_path: Where to save the .mp3 (auto-generated if None)

    Returns:
        Path to the generated .mp3 file
    """
    # Get voice for language
    voices = VOICES.get(lang, DEFAULT_VOICE)
    voice = voices[0] if voice_type == "grandma" else voices[1]

    # Generate output path if not provided
    if output_path is None:
        output_path = f"/tmp/story-{lang}-{voice_type}.mp3"

    # Run async generation
    asyncio.run(_generate_audio_async(text, voice, output_path))

    return output_path


def get_story_text(scenes: list) -> str:
    """Extract readable text from story scenes."""
    parts = []
    for scene in scenes:
        parts.append(scene.get("title", ""))
        parts.append(scene.get("description", ""))
    return ". ".join(parts)


if __name__ == "__main__":
    # Quick test
    test_text = "Das ist ein Weltraumforscher. Er ist unser Held!"
    output = generate_audio(test_text, lang="de", voice_type="grandma", output_path="/tmp/test-de.mp3")
    print(f"Generated: {output}")
