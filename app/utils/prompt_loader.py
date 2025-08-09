"""Prompt template loader and manager."""

import os
from typing import Dict, Optional

from loguru import logger


class PromptLoader:
    """Manages loading and caching of prompt templates."""
    
    def __init__(self, templates_dir: str = "data/prompts"):
        self.templates_dir = templates_dir
        self._cache: Dict[str, str] = {}
    
    def get_template(self, template_type: str, platform: str = "general") -> str:
        """Get a prompt template by type and platform."""
        cache_key = f"{template_type}_{platform}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Try to load platform-specific template first
        template_path = os.path.join(self.templates_dir, f"{template_type}_{platform}.txt")
        if not os.path.exists(template_path):
            # Fallback to general template
            template_path = os.path.join(self.templates_dir, f"{template_type}_general.txt")
        
        if not os.path.exists(template_path):
            # Return default template if file doesn't exist
            logger.warning(f"Template file not found: {template_path}, using default")
            template = self._get_default_template(template_type, platform)
        else:
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
            except Exception as e:
                logger.error(f"Failed to load template {template_path}: {str(e)}")
                template = self._get_default_template(template_type, platform)
        
        # Cache the template
        self._cache[cache_key] = template
        return template
    
    def _get_default_template(self, template_type: str, platform: str) -> str:
        """Get default template if file loading fails."""
        if template_type == "content_generation":
            return self._get_content_generation_template(platform)
        elif template_type == "hook_generation":
            return self._get_hook_generation_template(platform)
        elif template_type == "hashtag_generation":
            return self._get_hashtag_generation_template(platform)
        else:
            return "Generate content about {topic} for {platform} with {tone} tone targeting {target_audience}."
    
    def _get_content_generation_template(self, platform: str) -> str:
        """Default content generation template."""
        return """
You are an expert social media content creator specializing in {platform} content. Create a complete script for a viral {platform} video about "{topic}".

Content Requirements:
- Topic: {topic}
- Platform: {platform}
- Tone: {tone}
- Target Audience: {target_audience}
- Additional Requirements: {additional_requirements}

Platform Specifications:
{platform_specs}

Current Trends:
{trends_data}

Please generate a complete content package with the following structure:

HOOK (First 3-5 seconds):
[Create a compelling hook that grabs attention immediately and makes viewers want to watch more]

STORYLINE:
[Outline the main narrative structure and flow of the content]

SCRIPT:
[Write the complete script with clear, engaging narration that flows naturally]

HASHTAGS:
[Provide 5-10 relevant hashtags including trending and niche-specific tags]

Make sure the content is:
1. Platform-optimized for maximum engagement
2. Trend-aware and current
3. Audience-appropriate
4. Action-oriented with clear value proposition
5. Structured for the platform's algorithm

Focus on creating content that stops the scroll, delivers value, and encourages engagement.
"""
    
    def _get_hook_generation_template(self, platform: str) -> str:
        """Default hook generation template."""
        return """
Create 5 powerful hooks for a {platform} video about "{topic}" targeting {target_audience} with a {tone} tone.

Each hook should be:
- 3-5 seconds long when spoken
- Attention-grabbing from the first word
- Relevant to the topic
- Optimized for {platform}'s algorithm

Hooks should use techniques like:
- Questions that create curiosity
- Shocking statistics or facts
- Bold statements or claims
- Pattern interrupts
- Emotional triggers

Topic: {topic}
Platform: {platform}
Tone: {tone}
Target Audience: {target_audience}

Generate hooks that make viewers stop scrolling immediately.
"""
    
    def _get_hashtag_generation_template(self, platform: str) -> str:
        """Default hashtag generation template."""
        return """
Generate strategic hashtags for a {platform} video about "{topic}".

Consider:
- Topic: {topic}
- Platform: {platform}
- Target Audience: {target_audience}
- Current Trends: {trends_data}

Provide a mix of:
1. High-volume trending hashtags (2-3)
2. Medium-volume niche hashtags (3-4)
3. Low-volume specific hashtags (2-3)
4. Platform-specific hashtags (1-2)

Total: 8-12 hashtags optimized for discovery and engagement on {platform}.
"""