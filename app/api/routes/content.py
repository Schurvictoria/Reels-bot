"""Content generation API endpoints."""

import time
from typing import Optional
import inspect

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ContentGenerationError
from app.models.content import ContentScript, GenerationRequest
from app.services.content_generator import ContentGeneratorService

router = APIRouter()
async def _maybe_await(result):
    if inspect.isawaitable(result):
        return await result
    return result


class ContentGenerationRequest(BaseModel):
    """Request model for content generation."""
    topic: str = Field(..., min_length=1, max_length=200, description="Content topic")
    platform: str = Field(..., pattern=r"^(instagram|youtube|tiktok)$", description="Target platform")
    tone: str = Field(..., min_length=1, max_length=100, description="Content tone (e.g., casual, professional, funny)")
    target_audience: str = Field(..., min_length=1, max_length=200, description="Target audience description")
    additional_requirements: Optional[str] = Field(None, max_length=1000, description="Additional requirements")
    include_music: bool = Field(default=True, description="Include music suggestions")


class ContentGenerationResponse(BaseModel):
    """Response model for content generation."""
    success: bool
    request_id: int
    content: Optional[dict] = None
    error: Optional[str] = None
    generation_time: Optional[float] = None


@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request_data: ContentGenerationRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> ContentGenerationResponse:
    """Generate content script for social media reels."""
    start_time = time.time()

    gen_request = GenerationRequest(
        topic=request_data.topic,
        platform=request_data.platform,
        tone=request_data.tone,
        target_audience=request_data.target_audience,
        additional_requirements=request_data.additional_requirements,
        user_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        session_id=request.headers.get("session-id")
    )
    
    db.add(gen_request)
    await _maybe_await(db.commit())
    await _maybe_await(db.refresh(gen_request))
    
    try:
        content_service = ContentGeneratorService()
        trends = None

        content_result = await content_service.generate_content(
            topic=request_data.topic,
            platform=request_data.platform,
            tone=request_data.tone,
            target_audience=request_data.target_audience,
            additional_requirements=request_data.additional_requirements,
            include_music=request_data.include_music,
            trends=trends
        )

        generation_time = time.time() - start_time

        content_script = ContentScript(
            topic=request_data.topic,
            platform=request_data.platform,
            tone=request_data.tone,
            target_audience=request_data.target_audience,
            hook=content_result["hook"],
            storyline=content_result["storyline"],
            script=content_result["script"],
            timestamps=content_result.get("timestamps"),
            music_suggestions=content_result.get("music_suggestions"),
            hashtags=content_result.get("hashtags"),
            generation_time=int(generation_time),
            model_used=content_result.get("model_used"),
            quality_score=content_result.get("quality_score")
        )
        
        db.add(content_script)
        await _maybe_await(db.commit())
        await _maybe_await(db.refresh(content_script))

        gen_request.success = "success"
        gen_request.content_script_id = content_script.id
        gen_request.processing_time = int(generation_time * 1000)
        gen_request.completed_at = content_script.created_at
        await _maybe_await(db.commit())
        
        logger.info(f"Content generated successfully for request {gen_request.id}")
        
        return ContentGenerationResponse(
            success=True,
            request_id=gen_request.id,
            content=content_script.to_dict(),
            generation_time=generation_time
        )
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Content generation failed for request {gen_request.id}: {error_message}")

        gen_request.success = "failed"
        gen_request.error_message = error_message
        gen_request.processing_time = int((time.time() - start_time) * 1000)
        await _maybe_await(db.commit())
        
        if isinstance(e, ContentGenerationError):
            raise HTTPException(status_code=422, detail=error_message)
        else:
            raise HTTPException(status_code=500, detail="Internal server error during content generation")


@router.get("/scripts/{script_id}")
async def get_content_script(
    script_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get a content script by ID."""
    result = await _maybe_await(db.get(ContentScript, script_id))
    if not result:
        raise HTTPException(status_code=404, detail="Content script not found")
    
    return result.to_dict()


@router.get("/requests/{request_id}")
async def get_generation_request(
    request_id: int,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get a generation request by ID."""
    result = await _maybe_await(db.get(GenerationRequest, request_id))
    if not result:
        raise HTTPException(status_code=404, detail="Generation request not found")
    
    return result.to_dict()