from typing import Any, Dict

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel

from src.config.logs_config import get_logger
from src.execution.actions.process_wav_file_typhoon_action import (
    ProcessWavFileTyphoonAction,
)
from src.execution.usecases.process_wav_file_typhoon_usecase import (
    ProcessWavFileTyphoonUseCase,
)

router = APIRouter()
logger = get_logger(__name__)


class WavFileResponse(BaseModel):
    message: str
    file_info: Dict[str, Any]
    processing_status: str


async def get_process_wav_file_typhoon_usecase_with_manager(
    request: Request,
) -> ProcessWavFileTyphoonUseCase:
    asr_manager = getattr(request.app.state, "asr_manager", None)
    action = ProcessWavFileTyphoonAction(asr_manager=asr_manager)
    return ProcessWavFileTyphoonUseCase(action)


@router.post("", status_code=status.HTTP_200_OK)
async def process_wav_file_typhoon_endpoint(
    file: UploadFile = File(
        ..., description="WAV audio file to process with Typhoon only"
    ),
    include_transcript: bool = Query(
        False, description="Include structured transcript output"
    ),
    usecase: ProcessWavFileTyphoonUseCase = Depends(
        get_process_wav_file_typhoon_usecase_with_manager
    ),
):
    try:
        if not file.filename.endswith(".wav"):
            raise ValueError("Only .wav files are supported")

        logger.info(
            f"Received Typhoon-only WAV file: {file.filename}, size: {file.size}"
        )
        file_content = await file.read()
        result = await usecase.execute(
            file_content=file_content,
            filename=file.filename,
            include_transcript=include_transcript,
        )

        return WavFileResponse(
            message="WAV file processed successfully with Typhoon",
            file_info=result,
            processing_status="completed",
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing Typhoon WAV file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}",
        )
