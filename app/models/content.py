"""Content-related database models."""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class ContentScript(Base):
    """Model for storing generated content scripts."""
    
    __tablename__ = "content_scripts"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(200), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)  # instagram, youtube, tiktok
    tone = Column(String(100), nullable=False)
    target_audience = Column(String(200), nullable=False)
    
    # Generated content
    hook = Column(Text, nullable=False)
    storyline = Column(Text, nullable=False)
    script = Column(Text, nullable=False)
    timestamps = Column(JSON, nullable=True)  # List of timestamp objects
    music_suggestions = Column(JSON, nullable=True)  # List of music suggestions
    hashtags = Column(JSON, nullable=True)  # List of hashtags
    
    # Metadata
    generation_time = Column(Integer, nullable=True)  # Time taken to generate in seconds
    model_used = Column(String(100), nullable=True)
    quality_score = Column(Integer, nullable=True)  # 1-10 quality rating
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "topic": self.topic,
            "platform": self.platform,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "hook": self.hook,
            "storyline": self.storyline,
            "script": self.script,
            "timestamps": self.timestamps,
            "music_suggestions": self.music_suggestions,
            "hashtags": self.hashtags,
            "generation_time": self.generation_time,
            "model_used": self.model_used,
            "quality_score": self.quality_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class GenerationRequest(Base):
    """Model for tracking content generation requests."""
    
    __tablename__ = "generation_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Request parameters
    topic = Column(String(200), nullable=False)
    platform = Column(String(50), nullable=False)
    tone = Column(String(100), nullable=False)
    target_audience = Column(String(200), nullable=False)
    additional_requirements = Column(Text, nullable=True)
    
    # Request metadata
    user_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Response metadata
    success = Column(String(10), nullable=False, default="pending")  # pending, success, failed
    error_message = Column(Text, nullable=True)
    content_script_id = Column(Integer, nullable=True)  # Foreign key to ContentScript
    processing_time = Column(Integer, nullable=True)  # Processing time in milliseconds
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "topic": self.topic,
            "platform": self.platform,
            "tone": self.tone,
            "target_audience": self.target_audience,
            "additional_requirements": self.additional_requirements,
            "success": self.success,
            "error_message": self.error_message,
            "content_script_id": self.content_script_id,
            "processing_time": self.processing_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }