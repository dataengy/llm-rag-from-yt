#!/usr/bin/env python3
"""Fixed transcriber implementation based on working reference patterns."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Import common utilities
from utils import (
    setup_python_path, setup_logging, check_and_install_whisper,
    validate_audio_file, save_transcription_result, print_session_header
)

# Setup Python path and logging
setup_python_path()
log_file = setup_logging('transcriber_fix')

def create_fixed_transcriber():
    """Create a fixed version of our AudioTranscriber that handles dependencies properly."""
    
    # First ensure faster-whisper is available
    if not check_and_install_whisper():
        return None
    
    class FixedAudioTranscriber:
        """Fixed audio transcriber that handles dependencies properly."""
        
        def __init__(self, model_name: str = "base", device: str = "cpu", compute_type: str = "int8"):
            self.model_name = model_name
            self.device = device
            self.compute_type = compute_type
            self._model = None
        
        @property
        def model(self):
            """Lazy load whisper model with proper error handling."""
            if self._model is None:
                try:
                    from faster_whisper import WhisperModel
                    print(f"Loading Whisper model: {self.model_name}")
                    self._model = WhisperModel(
                        self.model_name, 
                        device=self.device, 
                        compute_type=self.compute_type
                    )
                    print(f"✅ Loaded Whisper model: {self.model_name}")
                except Exception as e:
                    print(f"❌ Failed to load Whisper model: {e}")
                    raise RuntimeError(f"Cannot load Whisper model: {e}") from e
            return self._model
        
        def transcribe_file(self, audio_path: Path, language: str = "ru", beam_size: int = 5, use_vad: bool = True) -> Optional[Dict[str, Any]]:
            """Transcribe a single audio file with proper error handling."""
            
            # Validate input
            if not validate_audio_file(audio_path):
                return None
            
            try:
                print(f"🔄 Transcribing {audio_path.name}...")
                
                # Perform transcription
                segments, info = self.model.transcribe(
                    str(audio_path),
                    language=None if language == "auto" else language,
                    beam_size=beam_size,
                    vad_filter=use_vad
                )
                
                # Collect results in our project's format
                transcription_segments = []
                full_text_parts = []
                
                for segment in segments:
                    text = (segment.text or "").strip()
                    if text:  # Only include non-empty segments
                        seg_data = {
                            "start": float(segment.start or 0.0),
                            "end": float(segment.end or 0.0), 
                            "speaker": "spk1",
                            "text": text,
                        }
                        transcription_segments.append(seg_data)
                        full_text_parts.append(text)
                
                # Build result in our project's expected format
                result = {
                    "file_id": audio_path.stem,
                    "language": getattr(info, "language", language),
                    "duration": getattr(info, "duration", 0.0),
                    "segments": transcription_segments,
                    "full_text": " ".join(full_text_parts).strip(),
                    "model": self.model_name,
                    "segment_count": len(transcription_segments)
                }
                
                print(f"✅ Transcribed {audio_path.name}: {len(transcription_segments)} segments, language: {result['language']}")
                return result
                
            except Exception as e:
                print(f"❌ Failed to transcribe {audio_path}: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        def save_transcription_file(self, result: Dict[str, Any], output_path: Path) -> bool:
            """Save transcription in readable format."""
            return save_transcription_result(result, output_path)
    
    return FixedAudioTranscriber

def test_fixed_transcriber():
    """Test the fixed transcriber with our audio file."""
    print_session_header("Testing Fixed Audio Transcriber")
    
    # Create fixed transcriber
    TranscriberClass = create_fixed_transcriber()
    if not TranscriberClass:
        print("❌ Cannot create transcriber - dependencies missing")
        return 1
    
    transcriber = TranscriberClass(model_name="base")
    
    # Test with our downloaded audio
    audio_file = Path("data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.mp3")
    
    if not audio_file.exists():
        print(f"❌ Test audio file not found: {audio_file}")
        return 1
    
    # Transcribe
    result = transcriber.transcribe_file(audio_file, language="ru")
    
    if not result:
        print("❌ Transcription failed")
        return 1
    
    # Save result
    output_path = Path("artifacts/testing/fixed_transcription.txt")
    if not transcriber.save_transcription_file(result, output_path):
        return 1
    
    # Show summary
    print("
📊 TRANSCRIPTION TEST RESULTS")
    print("=" * 50)
    print(f"✅ File ID: {result['file_id']}")
    print(f"✅ Language: {result['language']}")
    print(f"✅ Duration: {result['duration']:.2f}s")
    print(f"✅ Segments: {result['segment_count']}")
    print(f"✅ Characters: {len(result['full_text'])}")
    print(f"✅ Model: {result['model']}")
    print(f"✅ Output: {output_path}")
    
    print(f"
📝 SAMPLE TEXT:")
    print(f"{result['full_text'][:200]}...")
    
    return 0

if __name__ == "__main__":
    sys.exit(test_fixed_transcriber())
