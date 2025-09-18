"""Audio transcription using faster-whisper."""

from pathlib import Path

from loguru import logger


class AudioTranscriber:
    """Transcribes audio files using faster-whisper."""

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        """Initialize transcriber with model settings."""
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model = None

    @property
    def model(self):
        """Lazy load whisper model with proper dependency handling."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel

                logger.info(f"Loading Whisper model: {self.model_name}")
                self._model = WhisperModel(
                    self.model_name, device=self.device, compute_type=self.compute_type
                )
                logger.info(f"Loaded Whisper model: {self.model_name}")
            except ImportError as e:
                error_msg = (
                    "faster-whisper not installed. Install with: "
                    "pip install faster-whisper==1.0.3"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
            except Exception as e:
                error_msg = f"Failed to load Whisper model '{self.model_name}': {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        return self._model

    def transcribe_file(
        self,
        audio_path: Path,
        language: str = "ru",
        beam_size: int = 5,
        use_vad: bool = True,
    ) -> dict[str, any]:
        """Transcribe a single audio file.

        Args:
            audio_path: Path to audio file
            language: Language code for transcription
            beam_size: Beam size for decoding
            use_vad: Whether to use voice activity detection

        Returns:
            Dict with transcription results
        """
        try:
            logger.info(f"Transcribing {audio_path.name} (language: {language})")
            
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
                if text:  # Only include non-empty segments
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

            logger.info(
                f"Transcribed {audio_path.name}: {len(transcription_segments)} segments, "
                f"language: {result['language']}, duration: {result['duration']:.2f}s"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to transcribe {audio_path}: {e}")
            raise

    def transcribe_directory(
        self,
        input_dir: Path,
        language: str = "ru",
        beam_size: int = 5,
        use_vad: bool = False,
        use_fake: bool = False,
    ) -> dict[str, dict]:
        """Transcribe all audio files in a directory.

        Args:
            input_dir: Directory containing audio files
            language: Language code
            beam_size: Beam size for decoding
            use_vad: Whether to use VAD
            use_fake: Whether to use fake transcription for testing

        Returns:
            Dict mapping file_id to transcription results
        """
        results = {}
        audio_extensions = {".mp3", ".wav", ".m4a", ".mp4"}
        audio_files = [
            p
            for p in sorted(input_dir.glob("*"))
            if p.suffix.lower() in audio_extensions
        ]

        if not audio_files:
            logger.warning(f"No audio files found in {input_dir}")
            return results

        if use_fake:
            return self._create_fake_transcriptions(audio_files, language)

        for audio_file in audio_files:
            try:
                result = self.transcribe_file(audio_file, language, beam_size, use_vad)
                results[result["file_id"]] = result
            except Exception as e:
                logger.error(f"Skipping {audio_file}: {e}")
                continue

        return results

    def _create_fake_transcriptions(
        self, audio_files: list[Path], language: str
    ) -> dict[str, dict]:
        """Create fake transcriptions for testing."""
        results = {}
        for audio_file in audio_files:
            file_id = audio_file.stem
            result = {
                "file_id": file_id,
                "language": language,
                "segments": [
                    {
                        "start": 0.0,
                        "end": 5.0,
                        "speaker": "spk1",
                        "text": "(demo) пример транскрипта",
                    }
                ],
                "full_text": "(demo) пример транскрипта",
            }
            results[file_id] = result
            logger.info(f"Created fake transcription for {file_id}")

        return results
