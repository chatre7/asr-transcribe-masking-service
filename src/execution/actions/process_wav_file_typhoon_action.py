import gc
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil

from src.config.logs_config import get_logger
from src.models.asr_models import ASRModelManager
from src.utils.audio.chunk_wav_audio import chunk_wav_audio_bytes

logger = get_logger(__name__)


class ProcessWavFileTyphoonAction:
    def __init__(self, asr_manager: Optional[ASRModelManager] = None):
        self.max_memory_mb = 2048
        self.process = psutil.Process(os.getpid())
        self.asr_manager = asr_manager or ASRModelManager()

    def _check_memory_usage(self) -> None:
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            if memory_mb > self.max_memory_mb * 0.9:
                logger.error(
                    f"Critical memory usage: {memory_mb:.1f}MB / {self.max_memory_mb}MB"
                )
            elif memory_mb > self.max_memory_mb * 0.8:
                logger.warning(
                    f"High memory usage detected: {memory_mb:.1f}MB / {self.max_memory_mb}MB"
                )
        except Exception as e:
            logger.warning(f"Could not check memory usage: {e}")

    def _cleanup_memory(self) -> None:
        try:
            gc.collect()
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.debug(f"Memory after cleanup: {memory_mb:.1f}MB")
        except Exception as e:
            logger.warning(f"Memory cleanup failed: {e}")

    async def execute(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        logger.info(f"Executing Typhoon-only WAV transcription for: {filename}")
        self._check_memory_usage()

        start_time = datetime.now()
        results: List[Dict[str, Any]] = []
        model_processing_time_ms = 0.0

        try:
            chunk_info = chunk_wav_audio_bytes(
                wav_bytes=file_content,
                target_sr=16_000,
                chunk_duration_s=30,
                overlap_s=3,
                batch_size=3,
            )

            for chunk_batch in chunk_info["batch_generator"]():
                chunk_bytes_list = [chunk.to_bytes() for chunk in chunk_batch]
                chunk_meta_list = [chunk.to_dict() for chunk in chunk_batch]

                batch_results = await self.asr_manager.transcribe_chunks_parallel(
                    audio_chunks=chunk_bytes_list,
                    model_names=["typhoon"],
                )

                for i, (chunk_meta, trans_result) in enumerate(
                    zip(chunk_meta_list, batch_results)
                ):
                    transcriptions = trans_result.get("transcriptions", {})
                    processing_times = trans_result.get("processing_times_ms", {})
                    typhoon_result = transcriptions.get("typhoon", {})
                    placeholder_result = {"text": "", "error": "not_run"}

                    model_processing_time_ms += processing_times.get("typhoon", 0)

                    results.append(
                        {
                            "chunk_index": chunk_meta["chunk_index"],
                            "start_sec": chunk_meta["start_sec"],
                            "end_sec": chunk_meta["end_sec"],
                            "duration_sec": chunk_meta["duration_sec"],
                            "size_bytes": len(chunk_bytes_list[i]),
                            "transcriptions": {
                                "typhoon": typhoon_result,
                                "pathumma": placeholder_result,
                                "pathumma_noise": placeholder_result,
                            },
                            "processing_times_ms": {
                                "typhoon": processing_times.get("typhoon", 0),
                                "pathumma": 0,
                                "pathumma_noise": 0,
                            },
                        }
                    )

                del chunk_bytes_list
                del chunk_meta_list
                del chunk_batch

                self._cleanup_memory()

            chunk_dict = {}
            for item in results:
                chunk_id = item["chunk_index"]
                chunk_dict[chunk_id] = {
                    "chunk_info": {
                        "start_time": item["start_sec"],
                        "end_time": item["end_sec"],
                        "duration": item["duration_sec"],
                    },
                    "model_transcriptions": {
                        "typhoon": {
                            "text": item["transcriptions"]
                            .get("typhoon", {})
                            .get("text", "")
                        },
                        "pathumma": {"text": ""},
                        "pathumma_noise": {"text": ""},
                    },
                }

            end_time = datetime.now()
            total_processing_time_ms = 0.0
            time_diff = end_time - start_time
            if hasattr(time_diff, "total_seconds"):
                total_processing_time_ms = time_diff.total_seconds() * 1000

            return {
                "action": "wav_file_transcribed_typhoon",
                "filename": filename,
                "content_size": len(file_content),
                "status": "completed",
                "processing_summary": {
                    "total_chunks": len(results),
                    "chunk_duration_sec": 30,
                    "overlap_sec": 3,
                    "target_sample_rate": 16000,
                    "total_processing_time_ms": total_processing_time_ms,
                    "model_processing_times": {
                        "typhoon": model_processing_time_ms,
                        "pathumma": 0,
                        "pathumma_noise": 0,
                    },
                },
                "results": results,
                "chunk_dict": chunk_dict,
            }

        except Exception as e:
            logger.error(f"Error in Typhoon-only transcription: {e}")
            self._cleanup_memory()
            raise
