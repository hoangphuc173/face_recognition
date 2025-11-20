"""People management routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, status

from ...core.database_manager import DatabaseManager
from ...aws.dynamodb_client import DynamoDBClient
from ..schemas import DatabaseStats, PeopleListResponse, PersonResponse, PersonUpdate

router = APIRouter()
logger = logging.getLogger("api.people")

def get_db_manager() -> DatabaseManager:
    """Dependency provider for the DatabaseManager."""
    # In a real application, this might be a singleton or managed differently.
    dynamodb_client = DynamoDBClient()
    return DatabaseManager(aws_dynamodb_client=dynamodb_client)


@router.get("/people", response_model=PeopleListResponse)
async def list_people(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get list of all people in database."""
    try:
        people = db_manager.get_all_people()
        return PeopleListResponse(total=len(people), people=people)
    except Exception as e:
        logger.error(f"Error listing people: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list people: {str(e)}",
        )


@router.get("/people/{person_id}", response_model=PersonResponse)
async def get_person(
    person_id: str = PathParam(..., description="Person's unique ID"),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """Get detailed information about a specific person."""
    try:
        person = db_manager.get_person(person_id)
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person not found: {person_id}",
            )
        return person
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting person: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get person: {str(e)}",
        )


@router.put("/people/{person_id}", response_model=PersonResponse)
async def update_person(
    person_update: PersonUpdate,
    person_id: str = PathParam(..., description="Person's unique ID"),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """Update person's information."""
    try:
        if not db_manager.get_person(person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person not found: {person_id}",
            )

        update_data = person_update.dict(exclude_unset=True)
        if update_data:
            db_manager.update_person(person_id, update_data)

        updated_person = db_manager.get_person(person_id)
        if not updated_person:
            # This case should ideally not happen if the update is successful
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person '{person_id}' not found after update",
            )
        return updated_person
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating person: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update person: {str(e)}",
        )


@router.delete("/people/{person_id}")
async def delete_person(
    person_id: str = PathParam(..., description="Person's unique ID"),
    db_manager: DatabaseManager = Depends(get_db_manager),
):
    """Delete a person from the database."""
    try:
        if not db_manager.get_person(person_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Person not found: {person_id}",
            )

        db_manager.delete_person(person_id)

        logger.info(f"Person deleted: {person_id}")
        return {"success": True, "message": f"Person deleted: {person_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting person: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete person: {str(e)}",
        )


@router.get("/stats", response_model=DatabaseStats)
async def get_database_stats(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get database statistics."""
    try:
        people = db_manager.get_all_people()
        # In a real scenario, these would be calculated or aggregated differently
        return DatabaseStats(
            total_people=len(people),
            total_embeddings=sum(p.get('embedding_count', 0) for p in people),
            storage_size_mb=0.0,  # Placeholder
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )
