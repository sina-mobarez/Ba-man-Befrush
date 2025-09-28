import asyncio
import os
import tempfile
import logging
from typing import Optional
from pathlib import Path

import aiofiles
import torch
from transformers import pipeline
from pydub import AudioSegment
import librosa
import soundfile as sf

from core.config import settings

logger = logging.getLogger(__name__)


class SpeechService:
    def __init__(self):
        """
        Initialize the Persian Speech-to-Text service using Whisper model.
        """
        self._pipeline = None
        self.model_name = settings.WHISPER_MODEL_NAME
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_file_size_bytes = settings.AUDIO_MAX_FILE_SIZE_MB * 1024 * 1024
        self.max_duration_seconds = settings.AUDIO_MAX_DURATION_SECONDS
        logger.info(f"SpeechService initialized. Using device: {self.device}, Model: {self.model_name}")

    async def _get_pipeline(self):
        """
        Lazy initialization of the speech recognition pipeline.
        """
        if self._pipeline is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            # Run model loading in executor to avoid blocking
            loop = asyncio.get_event_loop()
            self._pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "automatic-speech-recognition",
                    model=self.model_name,
                    device=0 if self.device == "cuda" else -1,
                    return_timestamps=True
                )
            )
            logger.info("Whisper model loaded successfully")
        return self._pipeline

    async def download_voice_file(self, bot, file_id: str, voice_duration: int = None, voice_file_size: int = None) -> str:
        """
        Download voice file from Telegram and save to temporary location.

        Args:
            bot: Telegram bot instance
            file_id: Telegram file ID
            voice_duration: Duration of voice in seconds (for validation)
            voice_file_size: Size of voice file in bytes (for validation)

        Returns:
            Path to downloaded file

        Raises:
            ValueError: If file is too large or too long
        """
        try:
            # Validate file size
            if voice_file_size and voice_file_size > self.max_file_size_bytes:
                raise ValueError(f"فایل صوتی خیلی بزرگ است. حداکثر اندازه: {settings.AUDIO_MAX_FILE_SIZE_MB}MB")

            # Validate duration
            if voice_duration and voice_duration > self.max_duration_seconds:
                max_minutes = self.max_duration_seconds // 60
                raise ValueError(f"فایل صوتی خیلی طولانی است. حداکثر مدت: {max_minutes} دقیقه")

            # Get file info from Telegram
            file = await bot.get_file(file_id)

            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            temp_file_path = os.path.join(temp_dir, f"voice_{file_id}.ogg")

            # Download file
            await bot.download_file(file.file_path, temp_file_path)

            logger.info(f"Voice file downloaded: {temp_file_path}")
            return temp_file_path

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Error downloading voice file: {e}")
            raise

    async def convert_audio_format(self, input_path: str) -> str:
        """
        Convert audio file to WAV format for Whisper processing.

        Args:
            input_path: Path to input audio file

        Returns:
            Path to converted WAV file
        """
        try:
            # Generate output path
            output_path = input_path.rsplit('.', 1)[0] + '.wav'

            # Run conversion in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._convert_audio_sync,
                input_path,
                output_path
            )

            logger.info(f"Audio converted to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error converting audio format: {e}")
            raise

    def _convert_audio_sync(self, input_path: str, output_path: str):
        """
        Synchronous audio conversion using pydub and librosa.
        """
        # Load audio with pydub (handles various formats)
        audio = AudioSegment.from_file(input_path)

        # Convert to mono and set sample rate to 16kHz (Whisper standard)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)

        # Export as WAV
        audio.export(output_path, format="wav")

    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe audio file to Persian text using Whisper.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcribed text in Persian
        """
        try:
            # Get the pipeline
            pipe = await self._get_pipeline()

            # Run transcription in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                pipe,
                audio_path
            )

            # Extract text from result
            text = result["text"].strip()

            logger.info(f"Transcription completed. Length: {len(text)} characters")
            logger.debug(f"Transcribed text: {text[:100]}...")

            return text

        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise

    async def process_voice_message(self, bot, file_id: str, voice_duration: int = None, voice_file_size: int = None) -> str:
        """
        Complete pipeline to process a Telegram voice message.

        Args:
            bot: Telegram bot instance
            file_id: Telegram voice message file ID
            voice_duration: Duration of voice in seconds (for validation)
            voice_file_size: Size of voice file in bytes (for validation)

        Returns:
            Transcribed Persian text
        """
        temp_files = []
        try:
            # Download voice file
            voice_file_path = await self.download_voice_file(bot, file_id, voice_duration, voice_file_size)
            temp_files.append(voice_file_path)

            # Convert to WAV format
            wav_file_path = await self.convert_audio_format(voice_file_path)
            temp_files.append(wav_file_path)

            # Transcribe audio
            transcribed_text = await self.transcribe_audio(wav_file_path)

            return transcribed_text

        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            raise

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    logger.warning(f"Could not clean up temp file {temp_file}: {e}")

            # Clean up temporary directories
            for temp_file in temp_files:
                try:
                    temp_dir = os.path.dirname(temp_file)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                        logger.debug(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Could not clean up temp directory: {e}")

    def cleanup_model(self):
        """
        Clean up model resources.
        """
        if self._pipeline is not None:
            del self._pipeline
            self._pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Speech model cleaned up")