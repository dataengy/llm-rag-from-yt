#!/usr/bin/env python3
"""Fixed transcriber implementation based on working reference patterns."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def check_and_install_whisper():
    """Check if faster-whisper is available and install if needed."""
    try:
        import faster_whisper
        return True
    except ImportError:
        print("Installing faster-whisper...")
        result = os.system("pip install faster-whisper==1.0.3")
        if result == 0:
            print("✅ faster-whisper installed successfully")
            import faster_whisper  # Test import
            return True
        else:
            print("❌ Failed to install faster-whisper")
            return False

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
        
        def validate_audio_file(self, file_path: Path) -> bool:
            """Validate audio file using basic checks."""
            if not file_path.exists():
                print(f"❌ File does not exist: {file_path}")
                return False
            
            # Check file size (basic validation)
            if file_path.stat().st_size == 0:
                print(f"❌ Empty file: {file_path}")
                return False
            
            # Check file extension
            valid_extensions = {'.mp3', '.wav', '.m4a', '.mp4'}
            if file_path.suffix.lower() not in valid_extensions:
                print(f"❌ Unsupported file type: {file_path.suffix}")
                return False
            
            print(f"✅ Audio file validation passed: {file_path.name}")
            return True
        
        def transcribe_file(self, audio_path: Path, language: str = "ru", beam_size: int = 5, use_vad: bool = True) -> Optional[Dict[str, Any]]:
            """Transcribe a single audio file with proper error handling."""
            
            # Validate input
            if not self.validate_audio_file(audio_path):
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
            try:
                with output_path.open("w", encoding="utf-8") as f:
                    f.write(f"# Transcription of {result['file_id']}\n")
                    f.write(f"# Language: {result['language']}, Duration: {result['duration']:.2f}s\n")
                    f.write(f"# Model: Whisper {result['model']}, Segments: {result['segment_count']}\n")
                    f.write(f"# Full text: {result['full_text']}\n")
                    f.write("\n")
                    
                    for seg in result['segments']:
                        f.write(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}\n")
                
                print(f"💾 Saved transcription to: {output_path}")
                return True
            except Exception as e:
                print(f"❌ Failed to save transcription: {e}")
                return False
    
    return FixedAudioTranscriber

def test_fixed_transcriber():
    """Test the fixed transcriber with our audio file."""
    print("🧪 Testing Fixed Audio Transcriber")
    print("=" * 50)
    
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
    print("\n📊 TRANSCRIPTION TEST RESULTS")
    print("=" * 50)
    print(f"✅ File ID: {result['file_id']}")
    print(f"✅ Language: {result['language']}")
    print(f"✅ Duration: {result['duration']:.2f}s")
    print(f"✅ Segments: {result['segment_count']}")
    print(f"✅ Characters: {len(result['full_text'])}")
    print(f"✅ Model: {result['model']}")
    print(f"✅ Output: {output_path}")
    
    print(f"\n📝 SAMPLE TEXT:")
    print(f"{result['full_text'][:200]}...")
    
    return 0

if __name__ == "__main__":
    sys.exit(test_fixed_transcriber())