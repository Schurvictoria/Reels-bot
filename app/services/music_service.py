"""Spotify API integration service for music suggestions."""

from typing import Dict, List, Optional

import spotipy
from loguru import logger
from spotipy.oauth2 import SpotifyClientCredentials

from app.core.config import get_settings


class MusicService:
    """Service for getting music suggestions from Spotify API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.spotify = None
        
        if self.settings.SPOTIFY_CLIENT_ID and self.settings.SPOTIFY_CLIENT_SECRET:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=self.settings.SPOTIFY_CLIENT_ID,
                    client_secret=self.settings.SPOTIFY_CLIENT_SECRET
                )
                self.spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            except Exception as e:
                logger.error(f"Failed to initialize Spotify API: {str(e)}")
    
    async def get_music_suggestions(
        self,
        topic: str,
        tone: str,
        platform: str,
        limit: int = 5
    ) -> List[Dict]:
        """Get music suggestions based on content topic and tone."""
        if not self.spotify:
            logger.warning("Spotify API not available")
            return self._get_fallback_suggestions(topic, tone, platform)
        
        try:
            # Map tone to Spotify audio features
            audio_features = self._map_tone_to_features(tone)
            
            # Search for tracks based on topic
            search_query = self._build_search_query(topic, tone, platform)
            
            results = self.spotify.search(
                q=search_query,
                type='track',
                limit=limit * 2,  # Get more results to filter
                market='US'
            )
            
            suggestions = []
            for track in results['tracks']['items']:
                if len(suggestions) >= limit:
                    break
                
                # Filter tracks by audio features if possible
                if self._is_suitable_track(track, audio_features, platform):
                    suggestion = {
                        "name": track['name'],
                        "artist": ', '.join([artist['name'] for artist in track['artists']]),
                        "spotify_url": track['external_urls']['spotify'],
                        "preview_url": track['preview_url'],
                        "duration_ms": track['duration_ms'],
                        "popularity": track['popularity'],
                        "energy_level": self._estimate_energy_level(track),
                        "platform_suitable": platform,
                        "tone_match": tone
                    }
                    suggestions.append(suggestion)
            
            if not suggestions:
                return self._get_fallback_suggestions(topic, tone, platform)
            
            logger.info(f"Found {len(suggestions)} music suggestions for {topic}")
            return suggestions
            
        except Exception as e:
            logger.error(f"Spotify API request failed: {str(e)}")
            return self._get_fallback_suggestions(topic, tone, platform)
    
    def _map_tone_to_features(self, tone: str) -> Dict:
        """Map content tone to Spotify audio features."""
        tone_mappings = {
            "energetic": {"energy": (0.7, 1.0), "valence": (0.6, 1.0), "tempo": (120, 180)},
            "calm": {"energy": (0.0, 0.4), "valence": (0.3, 0.7), "tempo": (60, 100)},
            "happy": {"energy": (0.5, 1.0), "valence": (0.7, 1.0), "tempo": (100, 160)},
            "sad": {"energy": (0.0, 0.5), "valence": (0.0, 0.3), "tempo": (60, 100)},
            "motivational": {"energy": (0.6, 1.0), "valence": (0.5, 1.0), "tempo": (110, 170)},
            "relaxed": {"energy": (0.0, 0.5), "valence": (0.4, 0.8), "tempo": (70, 110)},
            "upbeat": {"energy": (0.7, 1.0), "valence": (0.6, 1.0), "tempo": (120, 180)},
            "chill": {"energy": (0.2, 0.6), "valence": (0.4, 0.7), "tempo": (80, 120)}
        }
        
        # Find the best matching tone
        tone_lower = tone.lower()
        for mapped_tone, features in tone_mappings.items():
            if mapped_tone in tone_lower or tone_lower in mapped_tone:
                return features
        
        # Default to moderate values
        return {"energy": (0.3, 0.7), "valence": (0.3, 0.7), "tempo": (90, 130)}
    
    def _build_search_query(self, topic: str, tone: str, platform: str) -> str:
        """Build Spotify search query based on content parameters."""
        # Base search with topic
        query_parts = [topic]
        
        # Add tone-related keywords
        tone_keywords = {
            "energetic": ["upbeat", "energy", "pump"],
            "calm": ["chill", "ambient", "peaceful"],
            "happy": ["happy", "joyful", "uplifting"],
            "sad": ["melancholy", "emotional", "slow"],
            "motivational": ["motivational", "inspiring", "powerful"],
            "funny": ["fun", "comedy", "playful"],
            "professional": ["corporate", "business", "clean"],
            "casual": ["casual", "everyday", "simple"]
        }
        
        tone_lower = tone.lower()
        for mapped_tone, keywords in tone_keywords.items():
            if mapped_tone in tone_lower:
                query_parts.extend(keywords[:2])
                break
        
        # Add platform-specific preferences
        platform_keywords = {
            "tiktok": ["viral", "trending", "popular"],
            "instagram": ["trendy", "lifestyle", "modern"],
            "youtube": ["background", "intro", "outro"]
        }
        
        if platform in platform_keywords:
            query_parts.extend(platform_keywords[platform][:1])
        
        return ' '.join(query_parts[:5])  # Limit query length
    
    def _is_suitable_track(self, track: Dict, target_features: Dict, platform: str) -> bool:
        """Check if track is suitable based on platform and features."""
        # Check duration (prefer shorter tracks for social media)
        duration_limits = {
            "tiktok": 60000,  # 60 seconds
            "instagram": 90000,  # 90 seconds
            "youtube": 120000  # 2 minutes
        }
        
        max_duration = duration_limits.get(platform, 90000)
        if track['duration_ms'] > max_duration:
            return False
        
        # Check if track has preview (indicates availability)
        if not track.get('preview_url'):
            return False
        
        # Check popularity (prefer moderately to highly popular tracks)
        if track.get('popularity', 0) < 20:
            return False
        
        return True
    
    def _estimate_energy_level(self, track: Dict) -> str:
        """Estimate energy level based on available track data."""
        # This is a simplified estimation based on available data
        popularity = track.get('popularity', 0)
        
        if popularity > 70:
            return "high"
        elif popularity > 40:
            return "medium"
        else:
            return "low"
    
    def _get_fallback_suggestions(self, topic: str, tone: str, platform: str) -> List[Dict]:
        """Get fallback music suggestions when Spotify API is not available."""
        fallback_suggestions = [
            {
                "name": "Upbeat Background Track",
                "artist": "Generic Artist",
                "spotify_url": "",
                "preview_url": "",
                "duration_ms": 60000,
                "popularity": 50,
                "energy_level": "medium",
                "platform_suitable": platform,
                "tone_match": tone,
                "note": "Spotify API not available - generic suggestion"
            }
        ]
        
        # Add tone-specific suggestions
        tone_suggestions = {
            "energetic": [
                {"name": "High Energy Beat", "energy_level": "high"},
                {"name": "Pump Up Track", "energy_level": "high"}
            ],
            "calm": [
                {"name": "Peaceful Ambient", "energy_level": "low"},
                {"name": "Gentle Background", "energy_level": "low"}
            ],
            "happy": [
                {"name": "Joyful Melody", "energy_level": "medium"},
                {"name": "Uplifting Tune", "energy_level": "medium"}
            ]
        }
        
        tone_lower = tone.lower()
        for mapped_tone, suggestions in tone_suggestions.items():
            if mapped_tone in tone_lower:
                for suggestion in suggestions:
                    base_suggestion = fallback_suggestions[0].copy()
                    base_suggestion.update(suggestion)
                    fallback_suggestions.append(base_suggestion)
                break
        
        return fallback_suggestions[:3]
    
    async def get_trending_music(self, platform: str, limit: int = 10) -> List[Dict]:
        """Get trending music for specific platform."""
        if not self.spotify:
            return []
        
        try:
            # Get featured playlists (trending music)
            playlists = self.spotify.featured_playlists(limit=5)
            
            trending_tracks = []
            for playlist in playlists['playlists']['items']:
                tracks = self.spotify.playlist_tracks(playlist['id'], limit=2)
                
                for item in tracks['items']:
                    track = item['track']
                    if track and len(trending_tracks) < limit:
                        trending_tracks.append({
                            "name": track['name'],
                            "artist": ', '.join([artist['name'] for artist in track['artists']]),
                            "spotify_url": track['external_urls']['spotify'],
                            "popularity": track['popularity'],
                            "from_playlist": playlist['name']
                        })
            
            return trending_tracks
            
        except Exception as e:
            logger.error(f"Failed to get trending music: {str(e)}")
            return []