"""User-related database models."""

from datetime import datetime
from typing import Dict

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """Model for user tracking and analytics."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # User identification (for analytics, not auth)
    session_id = Column(String(100), unique=True, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    
    # Usage statistics
    total_requests = Column(Integer, default=0)
    successful_generations = Column(Integer, default=0)
    failed_generations = Column(Integer, default=0)
    
    # Preferences (learned from usage)
    preferred_platform = Column(String(50), nullable=True)
    preferred_tone = Column(String(100), nullable=True)
    common_topics = Column(String(500), nullable=True)  # Comma-separated
    
    # Timestamps
    first_visit = Column(DateTime(timezone=True), server_default=func.now())
    last_visit = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "total_requests": self.total_requests,
            "successful_generations": self.successful_generations,
            "failed_generations": self.failed_generations,
            "preferred_platform": self.preferred_platform,
            "preferred_tone": self.preferred_tone,
            "common_topics": self.common_topics,
            "first_visit": self.first_visit.isoformat() if self.first_visit else None,
            "last_visit": self.last_visit.isoformat() if self.last_visit else None,
        }