"""Post-processing for raw transcripts.

Whisper output is generally clean, but it adds leading/trailing whitespace,
sometimes emits a stray transcript for near-silence, and does not know whether
the user wants a leading capital or a trailing space to chain phrases. This
module keeps that formatting logic in one easily testable place.
"""

from __future__ import annotations

# Phrases Whisper commonly hallucinates from silence or background noise.
# These are dropped only when they are the *entire* transcript.
_SILENCE_HALLUCINATIONS = {
    "you",
    "thank you.",
    "thanks for watching!",
    "thank you for watching.",
    "thank you for watching!",
    "please subscribe.",
    ".",
    "...",
}


def clean_transcript(
    raw: str,
    *,
    capitalize_first: bool = True,
    trailing_space: bool = True,
) -> str:
    """Normalize a raw transcript into text ready to type.

    Returns an empty string when the transcript is empty or looks like a
    silence hallucination, so callers can simply skip empty results.
    """
    text = (raw or "").strip()
    if not text:
        return ""

    # Drop common silence/noise hallucinations when they are the whole output.
    if text.lower() in _SILENCE_HALLUCINATIONS:
        return ""

    # Collapse internal runs of whitespace (incl. newlines) into single spaces.
    text = " ".join(text.split())

    if capitalize_first:
        text = text[0].upper() + text[1:]

    if trailing_space:
        text = text + " "

    return text
