from typing import Any, Dict

from src.config.logs_config import get_logger
from src.execution.actions.process_wav_file_typhoon_action import (
    ProcessWavFileTyphoonAction,
)
from src.utils.transcript.prase_transcript import parse_transcription

logger = get_logger(__name__)


class ProcessWavFileTyphoonUseCase:
    def __init__(self, action: ProcessWavFileTyphoonAction):
        self.action = action

    async def execute(
        self,
        file_content: bytes,
        filename: str,
        include_transcript: bool = False,
    ) -> Dict[str, Any]:
        logger.info(f"Starting Typhoon-only WAV processing for: {filename}")

        if not file_content:
            raise ValueError("File content is empty")

        if len(file_content) < 44:
            raise ValueError("File too small to be a valid WAV file")

        if not file_content[:4] == b"RIFF" or not file_content[8:12] == b"WAVE":
            raise ValueError("Invalid WAV file format")

        file_info = {
            "filename": filename,
            "size_bytes": len(file_content),
            "size_mb": round(len(file_content) / (1024 * 1024), 2),
            "file_type": "WAV",
            "validation": "passed",
        }

        result = await self.action.execute(file_content, filename)

        transcript = None
        if include_transcript:
            transcript_text = self._build_transcript_text(result.get("results", []))
            if transcript_text:
                transcript = parse_transcription(transcript_text)

        return {
            **file_info,
            "processing_stage": "completed",
            "chunk_processing": result,
            "next_steps": ["typhoon_transcription_completed"],
            "transcript": transcript,
        }

    def _build_transcript_text(self, results: list) -> str:
        lines = []
        for item in sorted(results, key=lambda x: x.get("chunk_index", 0)):
            text = item.get("transcriptions", {}).get("typhoon", {}).get("text", "")
            if not text:
                continue
            start_sec = float(item.get("start_sec", 0))
            end_sec = float(item.get("end_sec", 0))
            lines.append(f"[{start_sec:.2f} --> {end_sec:.2f}] [Unknown]: {text}")
        return "\n".join(lines)
