"""Face identification routes."""

import logging
import time

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ...core.identification_service import IdentificationService
from ..schemas import IdentificationResponse
from ..dependencies import get_identification_service

router = APIRouter()
logger = logging.getLogger("api.identify")


@router.post("/identify", response_model=IdentificationResponse)
async def identify_face(
    image: UploadFile = File(..., description="Image to identify faces from"),
    threshold: float = Form(
        default=90.0, description="Recognition confidence threshold (0-100)"
    ),
    identification_service: IdentificationService = Depends(get_identification_service),
):
    """Identify faces in an image using the AWS Rekognition backend."""
    start_time = time.time()

    try:
        image_bytes = await image.read()

        result = identification_service.identify_face(
            image_bytes=image_bytes, confidence_threshold=threshold
        )

        processing_time = (time.time() - start_time) * 1000

        if result.get("success"):
            faces_detected = result.get("faces_detected", len(result.get("faces", [])))
            logger.info(
                f"Identification complete: {faces_detected} faces identified "
                f"({processing_time:.2f}ms)"
            )
            return IdentificationResponse(
                success=True,
                faces_detected=faces_detected,
                faces=result.get("faces", []),
                processing_time_ms=processing_time,
            )
        else:
            logger.error(f"Identification failed: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Identification failed due to an unknown error."),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during identification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
