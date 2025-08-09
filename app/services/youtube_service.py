"""YouTube Data API integration service."""

from typing import Dict, List, Optional

import httpx
from googleapiclient.discovery import build
from loguru import logger

from app.core.config import get_settings


class YouTubeService:
    """Service for interacting with YouTube Data API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.YOUTUBE_API_KEY
        self.youtube = None
        
        if self.api_key:
            try:
                self.youtube = build('youtube', 'v3', developerKey=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize YouTube API: {str(e)}")
    
    async def get_trending_topics(self, topic: str, max_results: int = 10) -> Dict:
        """Get trending topics related to the search term."""
        if not self.youtube:
            logger.warning("YouTube API not available")
            return {
                "hashtags": [f"{topic}youtube", f"{topic}shorts"],
                "topics": [topic],
                "engagement_tips": "Use engaging thumbnails and titles"
            }
        
        try:
            # Search for videos related to the topic
            search_response = self.youtube.search().list(
                q=f"{topic} shorts",
                part='snippet',
                type='video',
                maxResults=max_results,
                order='relevance',
                videoDuration='short'  # For YouTube Shorts
            ).execute()
            
            hashtags = set()
            topics = set()
            
            for item in search_response.get('items', []):
                snippet = item['snippet']
                title = snippet.get('title', '')
                description = snippet.get('description', '')
                
                # Extract hashtags from title and description
                words = (title + ' ' + description).split()
                for word in words:
                    if word.startswith('#') and len(word) > 1:
                        hashtags.add(word[1:].lower())
                
                # Add title as potential topic
                if title:
                    topics.add(title)
            
            # Get video statistics for engagement insights
            engagement_tips = await self._analyze_engagement_patterns(search_response)
            
            return {
                "hashtags": list(hashtags)[:10],
                "topics": list(topics)[:5],
                "engagement_tips": engagement_tips,
                "trending_audio": [],
                "popular_creators": []
            }
            
        except Exception as e:
            logger.error(f"YouTube API request failed: {str(e)}")
            return {
                "hashtags": [f"{topic}youtube", f"{topic}shorts"],
                "topics": [topic],
                "engagement_tips": "Use engaging thumbnails and titles"
            }
    
    async def _analyze_engagement_patterns(self, search_response: Dict) -> str:
        """Analyze engagement patterns from search results."""
        try:
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            if not video_ids:
                return "Focus on engaging thumbnails and clear titles"
            
            # Get video statistics
            stats_response = self.youtube.videos().list(
                part='statistics',
                id=','.join(video_ids[:5])  # Limit to first 5 videos
            ).execute()
            
            total_views = 0
            total_likes = 0
            total_comments = 0
            video_count = 0
            
            for item in stats_response.get('items', []):
                stats = item.get('statistics', {})
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                total_views += views
                total_likes += likes
                total_comments += comments
                video_count += 1
            
            if video_count > 0:
                avg_engagement = (total_likes + total_comments) / total_views * 100 if total_views > 0 else 0
                
                if avg_engagement > 5:
                    return "High engagement content works well - focus on interactive elements"
                elif avg_engagement > 2:
                    return "Moderate engagement - add call-to-actions and questions"
                else:
                    return "Focus on hook optimization and audience retention"
            
            return "Focus on engaging thumbnails and clear titles"
            
        except Exception as e:
            logger.error(f"Failed to analyze engagement patterns: {str(e)}")
            return "Focus on engaging thumbnails and clear titles"
    
    async def get_channel_insights(self, channel_name: str) -> Dict:
        """Get insights from a specific YouTube channel."""
        if not self.youtube:
            return {}
        
        try:
            # Search for the channel
            search_response = self.youtube.search().list(
                q=channel_name,
                part='snippet',
                type='channel',
                maxResults=1
            ).execute()
            
            if not search_response.get('items'):
                return {}
            
            channel_id = search_response['items'][0]['id']['channelId']
            
            # Get channel statistics
            channel_response = self.youtube.channels().list(
                part='statistics,snippet',
                id=channel_id
            ).execute()
            
            if channel_response.get('items'):
                channel_data = channel_response['items'][0]
                stats = channel_data.get('statistics', {})
                
                return {
                    "subscriber_count": int(stats.get('subscriberCount', 0)),
                    "video_count": int(stats.get('videoCount', 0)),
                    "view_count": int(stats.get('viewCount', 0)),
                    "channel_name": channel_data['snippet'].get('title', ''),
                    "description": channel_data['snippet'].get('description', '')
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Failed to get channel insights: {str(e)}")
            return {}