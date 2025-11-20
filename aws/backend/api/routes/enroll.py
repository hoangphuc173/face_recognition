"""Face enrollment routes."""

import logging
import time
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ...core.enrollment_service import EnrollmentService
from ..schemas import EnrollmentResponse
from ..dependencies import get_enrollment_service

router = APIRouter()
logger = logging.getLogger("api.enroll")


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll_face(
    image: UploadFile = File(..., description="Face image file (JPG, PNG)"),
    user_name: str = Form(..., description="Full name of the person"),
    gender: Optional[str] = Form("", description="Gender (optional)"),
    birth_year: Optional[str] = Form("", description="Birth year (optional)"),
    hometown: Optional[str] = Form("", description="Hometown (optional)"),
    residence: Optional[str] = Form("", description="Current residence (optional)"),
    enrollment_service: EnrollmentService = Depends(get_enrollment_service),
):
    """Enroll a new face into the system by uploading an image."""
    start_time = time.time()

    try:
        image_bytes = await image.read()

        # The EnrollmentService is now injected and can be mocked in tests
        result = enrollment_service.enroll_face(
            image_bytes=image_bytes,
            user_name=user_name,
            gender=gender or "",
            birth_year=birth_year or "",
            hometown=hometown or "",
            residence=residence or "",
        )

        processing_time = (time.time() - start_time) * 1000

        if result.get("success"):
            logger.info(
                f"Enrollment successful for {user_name} -> {result.get('person_id')} "
                f"({processing_time:.2f}ms)"
            )
            return EnrollmentResponse(
                success=True,
                user_name=result.get("user_name", user_name),
                person_id=result.get("person_id"),
                face_id=result.get("face_id"),
                message=result.get("message"),
                duplicate_found=result.get("duplicate_found", False),
                duplicate_info=result.get("duplicate_info"),
                image_url=result.get("image_url"),
                quality_score=result.get("quality_score"),
                processing_time_ms=processing_time,
            )
        else:
            logger.error(f"Enrollment failed for {user_name}: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Enrollment failed due to an unknown error."),
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred during enrollment: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )
