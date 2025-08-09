"""Unit tests for content generator service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.content_generator import ContentGeneratorService
from app.core.exceptions import ContentGenerationError


class TestContentGeneratorService:
    """Test cases for ContentGeneratorService."""
    
    @pytest.fixture
    def content_service(self):
        """Create a ContentGeneratorService instance for testing."""
        with patch('app.services.content_generator.get_settings') as mock_settings:
            mock_settings.return_value.OPENAI_API_KEY = "test-key"
            mock_settings.return_value.OPENAI_MODEL = "gpt-4o"
            mock_settings.return_value.OPENAI_TEMPERATURE = 0.7
            mock_settings.return_value.OPENAI_MAX_TOKENS = 2000
            mock_settings.return_value.SPOTIFY_CLIENT_ID = "test-client"
            mock_settings.return_value.WANDB_API_KEY = None
            mock_settings.return_value.DEBUG = False
            
            with patch('app.services.content_generator.ChatOpenAI'):
                with patch('app.services.content_generator.MusicService'):
                    service = ContentGeneratorService()
                    return service
    
    @pytest.mark.asyncio
    async def test_generate_content_success(self, content_service):
        """Test successful content generation."""
        # Mock LLM response
        mock_response = """
        HOOK: Did you know this simple morning hack can change your entire day?
        
        STORYLINE: Start with the problem of feeling sluggish in the morning, introduce the 5-minute routine, show the transformation.
        
        SCRIPT: Every morning, millions of people wake up feeling tired and unmotivated. But what if I told you there's a simple 5-minute routine that can completely transform your energy levels? Here's what successful people do differently. First, they drink a full glass of water immediately upon waking. Second, they do 10 jumping jacks to get their blood flowing. Third, they write down three things they're grateful for. Try this tomorrow morning and watch how different you feel. Your future self will thank you!
        
        HASHTAGS: #morningroutine #productivity #healthyhabits #motivation #selfcare
        """
        
        with patch.object(content_service, 'memory'):
            with patch('app.services.content_generator.LLMChain') as mock_chain_class:
                mock_chain = MagicMock()
                mock_chain.arun = AsyncMock(return_value=mock_response)
                mock_chain_class.return_value = mock_chain
                
                result = await content_service.generate_content(
                    topic="5-minute morning routine",
                    platform="instagram",
                    tone="energetic",
                    target_audience="busy professionals"
                )
        
        # Verify result structure
        assert isinstance(result, dict)
        assert "hook" in result
        assert "storyline" in result
        assert "script" in result
        assert "hashtags" in result
        assert "timestamps" in result
        assert "model_used" in result
        assert "quality_score" in result
        
        # Verify content quality
        assert len(result["hook"]) > 0
        assert len(result["script"]) > 50
        assert len(result["hashtags"]) > 0
        assert result["quality_score"] > 0
    
    @pytest.mark.asyncio
    async def test_generate_content_with_trends(self, content_service):
        """Test content generation with trend data."""
        mock_trends = {
            "hashtags": ["trending1", "trending2"],
            "topics": ["viral topic"],
            "engagement_tips": "Use call-to-action"
        }
        
        mock_response = "HOOK: Test hook\nSCRIPT: Test script\nHASHTAGS: #test #example"
        
        with patch.object(content_service, 'memory'):
            with patch('app.services.content_generator.LLMChain') as mock_chain_class:
                mock_chain = MagicMock()
                mock_chain.arun = AsyncMock(return_value=mock_response)
                mock_chain_class.return_value = mock_chain
                
                result = await content_service.generate_content(
                    topic="test topic",
                    platform="tiktok",
                    tone="casual",
                    target_audience="Gen Z",
                    trends=mock_trends
                )
        
        assert result is not None
        assert mock_chain.arun.called
    
    @pytest.mark.asyncio
    async def test_generate_content_llm_failure(self, content_service):
        """Test handling of LLM failures."""
        with patch.object(content_service, 'memory'):
            with patch('app.services.content_generator.LLMChain') as mock_chain_class:
                mock_chain = MagicMock()
                mock_chain.arun = AsyncMock(side_effect=Exception("LLM Error"))
                mock_chain_class.return_value = mock_chain
                
                with pytest.raises(ContentGenerationError):
                    await content_service.generate_content(
                        topic="test topic",
                        platform="instagram",
                        tone="casual",
                        target_audience="test audience"
                    )
    
    def test_get_platform_specs(self, content_service):
        """Test platform specifications generation."""
        instagram_specs = content_service._get_platform_specs("instagram")
        youtube_specs = content_service._get_platform_specs("youtube")
        tiktok_specs = content_service._get_platform_specs("tiktok")
        
        assert "Instagram Reels" in instagram_specs
        assert "YouTube Shorts" in youtube_specs
        assert "TikTok" in tiktok_specs
        assert "Duration" in instagram_specs
        assert "Duration" in youtube_specs
        assert "Duration" in tiktok_specs
    
    def test_parse_generated_content(self, content_service):
        """Test parsing of generated content."""
        raw_content = """
        HOOK: This is a test hook
        STORYLINE: This is the storyline
        SCRIPT: This is the complete script with multiple sentences. It has good content.
        HASHTAGS: #test #example #content
        """
        
        result = content_service._parse_generated_content(raw_content)
        
        assert result["hook"].strip() == "This is a test hook"
        assert result["storyline"].strip() == "This is the storyline"
        assert "test" in result["hashtags"]
        assert "example" in result["hashtags"]
        assert len(result["timestamps"]) > 0
    
    def test_parse_json_content(self, content_service):
        """Test parsing of JSON formatted content."""
        json_content = """{
            "hook": "JSON hook",
            "storyline": "JSON storyline",
            "script": "JSON script",
            "hashtags": ["json", "test"]
        }"""
        
        result = content_service._parse_generated_content(json_content)
        
        assert result["hook"] == "JSON hook"
        assert result["hashtags"] == ["json", "test"]
    
    def test_generate_timestamps(self, content_service):
        """Test timestamp generation."""
        script = "First sentence. Second sentence here. Third and final sentence."
        
        timestamps = content_service._generate_timestamps(script)
        
        assert len(timestamps) == 3
        assert timestamps[0]["start"] == 0
        assert timestamps[0]["text"] == "First sentence"
        assert timestamps[1]["start"] > 0
        assert timestamps[2]["start"] > timestamps[1]["start"]
    
    def test_calculate_quality_score(self, content_service):
        """Test quality score calculation."""
        # High quality content
        high_quality = {
            "hook": "Great hook that's long enough",
            "storyline": "Detailed storyline with good content",
            "script": "This is a comprehensive script with lots of valuable content that provides real value",
            "hashtags": ["tag1", "tag2", "tag3", "tag4"],
            "timestamps": [{"start": 0, "end": 5, "text": "test"}]
        }
        
        score = content_service._calculate_quality_score(high_quality)
        assert score >= 8  # Should be high quality
        
        # Low quality content
        low_quality = {
            "hook": "Short",
            "storyline": "Brief",
            "script": "Short script",
            "hashtags": ["one"],
            "timestamps": []
        }
        
        score = content_service._calculate_quality_score(low_quality)
        assert score <= 5  # Should be lower quality