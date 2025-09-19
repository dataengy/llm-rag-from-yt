#!/usr/bin/env python3
"""Test the fixed project transcriber with real audio."""

import sys
from pathlib import Path

# Import common utilities
from utils import (
    setup_python_path, setup_logging, check_and_install_whisper,
    validate_audio_file, save_transcription_result, print_session_header
)

# Setup Python path and logging
setup_python_path()
log_file = setup_logging('test_project_transcriber')

def test_project_transcriber():
    """Test our fixed project transcriber."""
    print_session_header("Testing Project AudioTranscriber")
    
    # Install faster-whisper if needed
    if not check_and_install_whisper():
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
        print(f"
📊 RESULTS:")
        print(f"File ID: {result['file_id']}")
        print(f"Language: {result['language']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Segments: {result['segment_count']}")
        print(f"Model: {result['model']}")
        print(f"Text length: {len(result['full_text'])} characters")
        
        print(f"
📝 SAMPLE TEXT (first 150 chars):")
        print(f"'{result['full_text'][:150]}...'")
        
        # Save result for verification
        output_file = Path("artifacts/testing/project_transcription_result.txt")
        if not save_transcription_result(result, output_file):
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_project_transcriber())
