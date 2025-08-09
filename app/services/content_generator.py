"""Content generation service using LangChain and OpenAI."""

import json
from typing import Dict, List, Optional

import wandb
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from app.core.config import get_settings
from app.core.exceptions import ContentGenerationError
from app.services.music_service import MusicService
from app.utils.prompt_loader import PromptLoader


class ContentGeneratorService:
    """Service for generating social media content using LangChain."""
    
    def __init__(self):
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            model_name=self.settings.OPENAI_MODEL,
            temperature=self.settings.OPENAI_TEMPERATURE,
            max_tokens=self.settings.OPENAI_MAX_TOKENS,
            openai_api_key=self.settings.OPENAI_API_KEY
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.prompt_loader = PromptLoader()
        self.music_service = MusicService()
    
    async def generate_content(
        self,
        topic: str,
        platform: str,
        tone: str,
        target_audience: str,
        additional_requirements: Optional[str] = None,
        include_music: bool = True,
        trends: Optional[Dict] = None
    ) -> Dict:
        """Generate complete content script for social media reel."""
        try:
            logger.info(f"Generating content for topic: {topic}, platform: {platform}")
            
            # Load platform-specific prompt template
            prompt_template = self.prompt_loader.get_template(
                template_type="content_generation",
                platform=platform
            )
            
            # Create LangChain prompt
            prompt = PromptTemplate(
                input_variables=[
                    "topic", "platform", "tone", "target_audience", 
                    "additional_requirements", "trends_data", "platform_specs"
                ],
                template=prompt_template
            )
            
            # Create LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt,
                memory=self.memory,
                verbose=self.settings.DEBUG
            )
            
            # Prepare platform specifications
            platform_specs = self._get_platform_specs(platform)
            
            # Prepare trends data
            trends_data = ""
            if trends:
                trends_data = f"""
Current Trends:
- Trending hashtags: {', '.join(trends.get('hashtags', [])[:5])}
- Popular topics: {', '.join(trends.get('topics', [])[:3])}
- Engagement patterns: {trends.get('engagement_tips', 'N/A')}
"""
            
            # Generate content using LangChain
            result = await chain.arun(
                topic=topic,
                platform=platform,
                tone=tone,
                target_audience=target_audience,
                additional_requirements=additional_requirements or "None",
                trends_data=trends_data,
                platform_specs=platform_specs
            )
            
            # Parse the generated content
            content = self._parse_generated_content(result)
            
            # Add music suggestions if requested
            if include_music and self.settings.SPOTIFY_CLIENT_ID:
                try:
                    music_suggestions = await self.music_service.get_music_suggestions(
                        topic=topic,
                        tone=tone,
                        platform=platform
                    )
                    content["music_suggestions"] = music_suggestions
                except Exception as e:
                    logger.warning(f"Failed to get music suggestions: {str(e)}")
                    content["music_suggestions"] = []
            
            # Add metadata
            content["model_used"] = self.settings.OPENAI_MODEL
            content["quality_score"] = self._calculate_quality_score(content)
            
            # Log to Weights & Biases if configured
            if self.settings.WANDB_API_KEY:
                wandb.log({
                    "content_generation": {
                        "topic": topic,
                        "platform": platform,
                        "tone": tone,
                        "quality_score": content["quality_score"],
                        "script_length": len(content.get("script", "")),
                        "hashtags_count": len(content.get("hashtags", []))
                    }
                })
            
            logger.info("Content generation completed successfully")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            raise ContentGenerationError(f"Failed to generate content: {str(e)}")
    
    def _get_platform_specs(self, platform: str) -> str:
        """Get platform-specific specifications."""
        specs = {
            "instagram": """
Instagram Reels Specifications:
- Duration: 15-90 seconds optimal
- Aspect ratio: 9:16 (vertical)
- Hook: First 3 seconds critical
- Text overlay: Keep minimal, use captions
- Trending audio: Essential for reach
- Hashtags: 3-5 targeted hashtags
""",
            "youtube": """
YouTube Shorts Specifications:
- Duration: Up to 60 seconds
- Aspect ratio: 9:16 (vertical)
- Hook: First 5 seconds crucial
- Title: Include keywords
- Description: Brief but descriptive
- Hashtags: #Shorts + 2-3 relevant tags
""",
            "tiktok": """
TikTok Specifications:
- Duration: 15-60 seconds optimal
- Aspect ratio: 9:16 (vertical)
- Hook: First 3 seconds vital
- Trending sounds: Use popular audio
- Effects: Use trending effects
- Hashtags: Mix trending + niche hashtags
"""
        }
        return specs.get(platform, specs["instagram"])
    
    def _parse_generated_content(self, raw_content: str) -> Dict:
        """Parse the generated content from LLM response."""
        try:
            # Try to parse as JSON first
            if raw_content.strip().startswith("{"):
                return json.loads(raw_content)
            
            # If not JSON, parse structured text
            content = {
                "hook": "",
                "storyline": "",
                "script": "",
                "timestamps": [],
                "hashtags": []
            }
            
            lines = raw_content.split("\n")
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if "hook:" in line.lower():
                    current_section = "hook"
                    content["hook"] = line.split(":", 1)[1].strip()
                elif "storyline:" in line.lower():
                    current_section = "storyline"
                    content["storyline"] = line.split(":", 1)[1].strip()
                elif "script:" in line.lower():
                    current_section = "script"
                    content["script"] = line.split(":", 1)[1].strip()
                elif "hashtags:" in line.lower():
                    current_section = "hashtags"
                    hashtag_text = line.split(":", 1)[1].strip()
                    content["hashtags"] = [tag.strip("#").strip() for tag in hashtag_text.split() if tag.startswith("#")]
                elif current_section and line:
                    # Continue building current section
                    if current_section in ["hook", "storyline", "script"]:
                        content[current_section] += " " + line
                    elif current_section == "hashtags" and line.startswith("#"):
                        content["hashtags"].extend([tag.strip("#").strip() for tag in line.split() if tag.startswith("#")])
            
            # Generate basic timestamps if script exists
            if content["script"]:
                content["timestamps"] = self._generate_timestamps(content["script"])
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to parse generated content: {str(e)}")
            raise ContentGenerationError("Failed to parse generated content")
    
    def _generate_timestamps(self, script: str) -> List[Dict]:
        """Generate basic timestamps for the script."""
        sentences = [s.strip() for s in script.split(".") if s.strip()]
        if not sentences:
            return []
        
        # Estimate 2-3 seconds per sentence for reels
        timestamps = []
        current_time = 0
        
        for i, sentence in enumerate(sentences):
            duration = max(2, min(4, len(sentence) // 20))  # 2-4 seconds based on length
            timestamps.append({
                "start": current_time,
                "end": current_time + duration,
                "text": sentence,
                "type": "narration"
            })
            current_time += duration
        
        return timestamps
    
    def _calculate_quality_score(self, content: Dict) -> int:
        """Calculate quality score based on content completeness and structure."""
        score = 0
        
        # Check for required elements
        if content.get("hook") and len(content["hook"]) > 10:
            score += 2
        if content.get("storyline") and len(content["storyline"]) > 20:
            score += 2
        if content.get("script") and len(content["script"]) > 50:
            score += 3
        if content.get("hashtags") and len(content["hashtags"]) >= 3:
            score += 2
        if content.get("timestamps"):
            score += 1
        
        return min(10, score)  # Cap at 10