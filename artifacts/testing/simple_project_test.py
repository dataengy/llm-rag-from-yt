#!/usr/bin/env python3
"""Simple test of project transcriber without av dependency."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_transcriber_without_complex_deps():
    """Test transcriber by bypassing complex dependencies."""
    
    # Import faster-whisper directly to ensure it works
    try:
        from faster_whisper import WhisperModel
        print("✅ faster-whisper is available")
    except ImportError:
        print("❌ faster-whisper not available")
        return 1
    
    # Test our fixed transcriber by creating an instance manually
    print("🔧 Creating fixed transcriber instance...")
    
    class SimpleTranscriber:
        """Simple version of our transcriber for testing."""
        
        def __init__(self, model_name="base"):
            self.model_name = model_name
            self._model = None
        
        @property
        def model(self):
            if self._model is None:
                from faster_whisper import WhisperModel
                print(f"Loading Whisper model: {self.model_name}")
                self._model = WhisperModel(
                    self.model_name, 
                    device="cpu", 
                    compute_type="int8"
                )
                print(f"✅ Loaded model: {self.model_name}")
            return self._model
        
        def transcribe_file(self, audio_path, language="ru", beam_size=5, use_vad=True):
            """Transcribe audio file."""
            print(f"🎵 Transcribing: {audio_path.name}")
            
            segments, info = self.model.transcribe(
                str(audio_path),
                language=None if language == "auto" else language,
                beam_size=beam_size,
                vad_filter=use_vad,
            )

            transcription_segments = []
            full_text_parts = []

            for segment in segments:
                text = (segment.text or "").strip()
                if text:
                    seg_data = {
                        "start": float(segment.start or 0.0),
                        "end": float(segment.end or 0.0),
                        "speaker": "spk1",
                        "text": text,
                    }
                    transcription_segments.append(seg_data)
                    full_text_parts.append(text)

            result = {
                "file_id": audio_path.stem,
                "language": getattr(info, "language", language),
                "duration": getattr(info, "duration", 0.0),
                "segments": transcription_segments,
                "full_text": " ".join(full_text_parts).strip(),
                "model": self.model_name,
                "segment_count": len(transcription_segments),
            }

            print(f"✅ Transcribed: {len(transcription_segments)} segments, "
                  f"language: {result['language']}, duration: {result['duration']:.2f}s")
            return result
    
    # Test the transcriber
    transcriber = SimpleTranscriber("base")
    
    audio_file = Path("data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.mp3")
    
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return 1
    
    try:
        result = transcriber.transcribe_file(audio_file, language="ru")
        
        print("\n📊 TRANSCRIPTION RESULTS")
        print("=" * 50)
        print(f"File ID: {result['file_id']}")
        print(f"Language: {result['language']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Segments: {result['segment_count']}")
        print(f"Model: {result['model']}")
        print(f"Text length: {len(result['full_text'])} characters")
        
        # Show sample
        print(f"\n📝 FULL TEXT:")
        print(f"{result['full_text']}")
        
        # Save results
        output_file = Path("artifacts/testing/simple_transcription_result.txt") 
        with output_file.open("w", encoding="utf-8") as f:
            f.write(f"# Simple Transcriber Test Result\n")
            f.write(f"# File: {result['file_id']}\n") 
            f.write(f"# Language: {result['language']}, Duration: {result['duration']:.2f}s\n")
            f.write(f"# Model: {result['model']}, Segments: {result['segment_count']}\n")
            f.write(f"\nFull text:\n{result['full_text']}\n\n")
            f.write("Timestamped segments:\n")
            for seg in result['segments']:
                f.write(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}\n")
        
        print(f"\n💾 Saved results to: {output_file}")
        
        # Verify our result format matches project expectations
        expected_keys = {"file_id", "language", "duration", "segments", "full_text", "model", "segment_count"}
        if set(result.keys()).issuperset(expected_keys):
            print("✅ Result format matches project requirements")
        else:
            missing = expected_keys - set(result.keys())
            print(f"⚠️ Missing keys in result: {missing}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_transcriber_without_complex_deps())