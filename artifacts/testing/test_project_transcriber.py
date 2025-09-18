#!/usr/bin/env python3
"""Test the fixed project transcriber with real audio."""

import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_project_transcriber():
    """Test our fixed project transcriber."""
    print("🧪 Testing Project AudioTranscriber")
    print("=" * 50)
    
    # Install faster-whisper if needed
    try:
        import faster_whisper
    except ImportError:
        import os
        print("📦 Installing faster-whisper...")
        result = os.system("pip install faster-whisper==1.0.3")
        if result != 0:
            print("❌ Failed to install faster-whisper")
            return 1
    
    try:
        from llm_rag_yt.audio.transcriber import AudioTranscriber
        print("✅ Successfully imported AudioTranscriber")
    except Exception as e:
        print(f"❌ Failed to import AudioTranscriber: {e}")
        return 1
    
    # Create transcriber instance
    try:
        transcriber = AudioTranscriber(
            model_name="base",
            device="cpu", 
            compute_type="int8"
        )
        print("✅ Created AudioTranscriber instance")
    except Exception as e:
        print(f"❌ Failed to create AudioTranscriber: {e}")
        return 1
    
    # Test transcription
    audio_file = Path("data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.mp3")
    
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return 1
    
    try:
        print(f"🎵 Transcribing: {audio_file.name}")
        result = transcriber.transcribe_file(
            audio_file, 
            language="ru", 
            beam_size=5, 
            use_vad=True
        )
        
        print("✅ Transcription completed successfully!")
        
        # Show results
        print(f"\n📊 RESULTS:")
        print(f"File ID: {result['file_id']}")
        print(f"Language: {result['language']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Segments: {result['segment_count']}")
        print(f"Model: {result['model']}")
        print(f"Text length: {len(result['full_text'])} characters")
        
        print(f"\n📝 SAMPLE TEXT (first 150 chars):")
        print(f"'{result['full_text'][:150]}...'")
        
        # Save result for verification
        output_file = Path("artifacts/testing/project_transcription_result.txt")
        with output_file.open("w", encoding="utf-8") as f:
            f.write(f"# Project Transcriber Test Result\n")
            f.write(f"# File: {result['file_id']}\n")
            f.write(f"# Language: {result['language']}, Duration: {result['duration']:.2f}s\n") 
            f.write(f"# Model: {result['model']}, Segments: {result['segment_count']}\n")
            f.write(f"\nFull text:\n{result['full_text']}\n\n")
            f.write("Segments:\n")
            for seg in result['segments']:
                f.write(f"[{seg['start']:.2f}-{seg['end']:.2f}] {seg['text']}\n")
        
        print(f"💾 Saved detailed results to: {output_file}")
        return 0
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_project_transcriber())