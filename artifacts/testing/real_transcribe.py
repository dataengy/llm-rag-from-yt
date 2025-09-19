#!/usr/bin/env python3
"""Real transcription script using faster-whisper without torch dependency issues."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Import common utilities
from utils import (
    setup_python_path, setup_logging, install_required_packages,
    validate_audio_file, save_transcription_result, print_session_header
)

# Setup Python path and logging
setup_python_path()
log_file = setup_logging('real_transcribe')

def install_requirements():
    """Install required packages for transcription."""
    packages = [
        ("faster_whisper", "faster-whisper==1.0.3"),
        ("av", "av")
    ]
    return install_required_packages(packages)

def validate_audio_file_advanced(file_path: Path) -> bool:
    """Validate that file is a proper audio file using av library."""
    try:
        import av
        with av.open(str(file_path), mode="r", metadata_errors="ignore") as container:
            # Check if it has audio streams
            if not container.streams.audio:
                print(f"❌ No audio streams found in {file_path}")
                return False
            
            # Try to get duration to ensure it's not corrupted
            duration = container.duration
            if duration is None or duration <= 0:
                print(f"❌ Invalid or zero duration in {file_path}")
                return False
            
            print(f"✅ Valid audio file: {file_path.name} (duration: {duration / av.time_base:.2f}s)")
            return True
            
    except Exception as e:
        print(f"❌ Audio validation failed for {file_path}: {e}")
        return False

def transcribe_audio_file(audio_path: Path, language: str = "auto", model_size: str = "base") -> Optional[Dict[str, Any]]:
    """Transcribe audio file using faster-whisper."""
    try:
        from faster_whisper import WhisperModel
        
        print(f"🎙️ Loading Whisper model: {model_size}")
        model = WhisperModel(
            model_size, 
            device="cpu",  # Use CPU to avoid CUDA issues
            compute_type="int8"  # Efficient CPU computation
        )
        
        print(f"🔄 Transcribing {audio_path.name}...")
        segments, info = model.transcribe(
            str(audio_path), 
            language=None if language == "auto" else language,
            beam_size=5,
            vad_filter=True  # Voice activity detection
        )
        
        # Collect transcription content
        transcription_lines = []
        transcription_lines.append(f"# Transcription of {audio_path.name}")
        transcription_lines.append(f"# Language: {info.language}, Duration: {info.duration:.2f}s")
        transcription_lines.append(f"# Model: Whisper {model_size}, VAD: True")
        transcription_lines.append("")
        
        segment_count = 0
        full_text_parts = []
        
        for seg in segments:
            text = seg.text.strip()
            if text:  # Only process non-empty segments
                timestamp_line = f"[{seg.start:.2f}-{seg.end:.2f}] {text}"
                transcription_lines.append(timestamp_line)
                full_text_parts.append(text)
                segment_count += 1
        
        if segment_count > 0:
            result = {
                'success': True,
                'input_file': str(audio_path),
                'language': info.language,
                'duration': info.duration,
                'segment_count': segment_count,
                'transcription_lines': transcription_lines,
                'full_text': ' '.join(full_text_parts),
                'model': model_size
            }
            print(f"✅ Successfully transcribed {segment_count} segments")
            return result
        else:
            print(f"❌ No segments transcribed from {audio_path.name}")
            return None
            
    except Exception as e:
        print(f"❌ Transcription failed for {audio_path.name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main transcription function."""
    print_session_header("Real Transcription Script for YouTube Audio")
    
    # Install requirements first
    if not install_requirements():
        print("❌ Failed to install requirements")
        return 1
    
    # Define audio file path
    audio_file = Path("data/audio/В месяц ты зарабатываешь больше 1млн рублей？ Звезда ＂Реутов ТВ＂ у Дудя.mp3")
    
    if not audio_file.exists():
        print(f"❌ Audio file not found: {audio_file}")
        return 1
    
    print(f"🎵 Processing audio file: {audio_file.name}")
    
    # Validate audio file first
    if not validate_audio_file_advanced(audio_file):
        print("❌ Audio file validation failed")
        return 1
    
    # Transcribe the audio
    result = transcribe_audio_file(audio_file, language="ru", model_size="base")
    
    if not result:
        print("❌ Transcription failed")
        return 1
    
    # Save transcription
    output_path = audio_file.with_suffix('.real_transcript.txt')
    if not save_transcription_result(result, output_path):
        return 1
    
    # Print summary
    print("
" + "=" * 50)
    print("📊 TRANSCRIPTION SUMMARY")
    print("=" * 50)
    print(f"Input file: {result['input_file']}")
    print(f"Output file: {output_path}")
    print(f"Language detected: {result['language']}")
    print(f"Duration: {result['duration']:.2f} seconds")
    print(f"Segments: {result['segment_count']}")
    print(f"Model used: Whisper {result['model']}")
    print(f"Characters: {len(result['full_text'])}")
    print(f"Words (approx): {len(result['full_text'].split())}")
    
    # Show first few lines of transcription
    print("
📝 TRANSCRIPTION PREVIEW:")
    print("-" * 30)
    lines = result['transcription_lines'][4:]  # Skip metadata lines
    for i, line in enumerate(lines[:5]):  # Show first 5 segments
        print(line)
    if len(lines) > 5:
        print(f"... and {len(lines) - 5} more segments")
    
    print("
✅ Real transcription completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
