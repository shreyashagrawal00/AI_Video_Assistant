import whisper
import os
import requests
from pydub import AudioSegment

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25


WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")


SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

_model = None


def load_model():

    global _model  

    if _model is None: 
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL) 
        print("Whisper model loaded.")
    return _model 


def transcribe_chunk_whisper(chunk_path: str, start_offset: float = 0.0) -> list:
    model = load_model()  
    result = model.transcribe(chunk_path, task="transcribe")  
    
    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"] + start_offset, 2),
            "end": round(seg["end"] + start_offset, 2),
            "text": seg["text"].strip()
        })
        
    if not segments and result.get("text"):
        segments.append({
            "start": round(start_offset, 2),
            "end": round(start_offset + 30.0, 2),
            "text": result["text"].strip()
        })
        
    return segments


def _send_to_sarvam(piece_path: str) -> str:
    """Send one ≤30s WAV file to Sarvam and return the English transcript."""
    headers = {"api-subscription-key": SARVAM_API_KEY}

    with open(piece_path, "rb") as f:
        files = {"file": (os.path.basename(piece_path), f, "audio/wav")}
        data = {"model": SARVAM_MODEL, "with_diarization": "false"}
        response = requests.post(
            SARVAM_STT_TRANSLATE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=120,
        )

    if not response.ok:
        print(f"\nERROR: Sarvam returned {response.status_code}")
        print(f"Response body: {response.text}\n")
        response.raise_for_status()

    return response.json().get("transcript", "")


def transcribe_chunk_sarvam(chunk_path: str, start_offset: float = 0.0) -> list:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    segments = []
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f"  → Sarvam piece {i + 1}/{total_pieces} ...")
            text = _send_to_sarvam(piece_path).strip()
            if text:
                seg_start = start_offset + (start / 1000.0)
                seg_end = start_offset + (min(start + piece_ms, len(audio)) / 1000.0)
                segments.append({
                    "start": round(seg_start, 2),
                    "end": round(seg_end, 2),
                    "text": text
                })
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return segments


def transcribe_chunk(chunk_path: str, language: str = "english", start_offset: float = 0.0) -> list:
    """
    Route one chunk to Whisper or Sarvam depending on language choice.
    - english  → Whisper (local model)
    - hinglish → Sarvam (translates to English while transcribing)
    """
    if language.lower() == "hinglish":
        return transcribe_chunk_sarvam(chunk_path, start_offset)
    return transcribe_chunk_whisper(chunk_path, start_offset)


def transcribe_all(chunks: list, language: str = "english", chunk_minutes: int = 10) -> dict:
    full_segments = []
    engine = "Sarvam AI" if language.lower() == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")

    for i, chunk in enumerate(chunks):  
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        start_offset = i * chunk_minutes * 60.0
        segments = transcribe_chunk(chunk, language=language, start_offset=start_offset)  
        full_segments.extend(segments)

    print("Transcription complete.")
    
    full_text = " ".join([seg["text"] for seg in full_segments])
    
    return {
        "text": full_text.strip(),
        "segments": full_segments
    }
