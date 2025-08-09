"""Gradio web interface for ReelsBot."""

import asyncio
import json
from typing import Optional, Tuple

import gradio as gr
import httpx
from loguru import logger

from app.core.config import get_settings


class ReelsBotInterface:
    """Gradio interface for ReelsBot application."""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.settings = get_settings()
    
    def create_interface(self) -> gr.Blocks:
        """Create and configure the Gradio interface."""
        
        with gr.Blocks(
            title="ReelsBot - AI Content Generator",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as interface:
            
            # Header
            gr.HTML("""
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1>🎬 ReelsBot</h1>
                    <p>AI-powered content generation for Instagram Reels, YouTube Shorts, and TikTok</p>
                </div>
            """)
            
            # Main interface
            with gr.Row():
                # Input column
                with gr.Column(scale=1):
                    gr.Markdown("### Content Parameters")
                    
                    topic = gr.Textbox(
                        label="Topic",
                        placeholder="E.g., 'Morning skincare routine', 'Cooking pasta', 'Productivity tips'",
                        lines=2
                    )
                    
                    platform = gr.Radio(
                        choices=["instagram", "youtube", "tiktok"],
                        label="Platform",
                        value="instagram"
                    )
                    
                    tone = gr.Dropdown(
                        choices=[
                            "casual", "professional", "funny", "energetic", 
                            "calm", "motivational", "educational", "trendy"
                        ],
                        label="Tone",
                        value="casual"
                    )
                    
                    target_audience = gr.Textbox(
                        label="Target Audience",
                        placeholder="E.g., 'Young professionals 25-35', 'Beauty enthusiasts', 'Fitness beginners'",
                        lines=2
                    )
                    
                    additional_requirements = gr.Textbox(
                        label="Additional Requirements (Optional)",
                        placeholder="Any specific requirements, style preferences, or constraints",
                        lines=3
                    )
                    
                    with gr.Row():
                        include_music = gr.Checkbox(label="Include Music Suggestions", value=True)
                        include_trends = gr.Checkbox(label="Include Trend Analysis", value=True)
                    
                    generate_btn = gr.Button("🎬 Generate Content", variant="primary", size="lg")
                
                # Output column
                with gr.Column(scale=1):
                    gr.Markdown("### Generated Content")
                    
                    # Status indicator
                    status = gr.Textbox(label="Status", interactive=False)
                    
                    # Content output tabs
                    with gr.Tabs():
                        with gr.TabItem("📝 Script"):
                            hook_output = gr.Textbox(label="Hook", lines=3, interactive=False)
                            storyline_output = gr.Textbox(label="Storyline", lines=4, interactive=False)
                            script_output = gr.Textbox(label="Complete Script", lines=8, interactive=False)
                        
                        with gr.TabItem("🏷️ Hashtags & Music"):
                            hashtags_output = gr.Textbox(label="Hashtags", lines=3, interactive=False)
                            music_output = gr.JSON(label="Music Suggestions")
                        
                        with gr.TabItem("⏱️ Timeline"):
                            timestamps_output = gr.JSON(label="Timestamps")
                        
                        with gr.TabItem("📊 Metadata"):
                            metadata_output = gr.JSON(label="Generation Details")
            
            # Examples section
            gr.Markdown("### Example Topics")
            gr.Examples(
                examples=[
                    ["5-minute morning routine", "instagram", "energetic", "Busy professionals", ""],
                    ["How to make perfect pasta", "youtube", "educational", "Cooking beginners", "Show close-up shots"],
                    ["Productivity hacks for students", "tiktok", "trendy", "College students", "Keep it under 30 seconds"],
                    ["Skincare routine for dry skin", "instagram", "calm", "Beauty enthusiasts", "Include product recommendations"]
                ],
                inputs=[topic, platform, tone, target_audience, additional_requirements]
            )
            
            # Event handlers
            generate_btn.click(
                fn=self.generate_content,
                inputs=[
                    topic, platform, tone, target_audience, 
                    additional_requirements, include_music, include_trends
                ],
                outputs=[
                    status, hook_output, storyline_output, script_output,
                    hashtags_output, music_output, timestamps_output, metadata_output
                ]
            )
        
        return interface
    
    def generate_content(
        self,
        topic: str,
        platform: str,
        tone: str,
        target_audience: str,
        additional_requirements: str,
        include_music: bool,
        include_trends: bool
    ) -> Tuple:
        """Generate content using the ReelsBot API."""
        try:
            # Validate inputs
            if not topic.strip():
                return ("❌ Error: Topic is required", "", "", "", "", {}, {}, {})
            
            if not target_audience.strip():
                return ("❌ Error: Target audience is required", "", "", "", "", {}, {}, {})
            
            # Update status
            status = "🔄 Generating content..."
            
            # Prepare request data
            request_data = {
                "topic": topic.strip(),
                "platform": platform,
                "tone": tone,
                "target_audience": target_audience.strip(),
                "additional_requirements": additional_requirements.strip() if additional_requirements else None,
                "include_music": include_music,
                "include_trends": include_trends
            }
            
            # Make API request
            response = asyncio.run(self._make_api_request(request_data))
            
            if response["success"]:
                content = response["content"]
                
                # Format hashtags
                hashtags_formatted = " ".join([f"#{tag}" for tag in content.get("hashtags", [])])
                
                # Prepare metadata
                metadata = {
                    "generation_time": response.get("generation_time"),
                    "model_used": content.get("model_used"),
                    "quality_score": content.get("quality_score"),
                    "request_id": response.get("request_id")
                }
                
                return (
                    "✅ Content generated successfully!",
                    content.get("hook", ""),
                    content.get("storyline", ""),
                    content.get("script", ""),
                    hashtags_formatted,
                    content.get("music_suggestions", []),
                    content.get("timestamps", []),
                    metadata
                )
            else:
                error_msg = response.get("error", "Unknown error occurred")
                return (f"❌ Error: {error_msg}", "", "", "", "", {}, {}, {})
        
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return (f"❌ Error: {str(e)}", "", "", "", "", {}, {}, {})
    
    async def _make_api_request(self, request_data: dict) -> dict:
        """Make request to the ReelsBot API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/content/generate",
                    json=request_data,
                    timeout=60.0
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.RequestError as e:
                logger.error(f"API request failed: {str(e)}")
                return {
                    "success": False,
                    "error": f"Failed to connect to API: {str(e)}"
                }
            
            except httpx.HTTPStatusError as e:
                logger.error(f"API returned error: {e.response.status_code}")
                try:
                    error_detail = e.response.json().get("detail", str(e))
                except:
                    error_detail = str(e)
                return {
                    "success": False,
                    "error": f"API error: {error_detail}"
                }
    
    def _get_custom_css(self) -> str:
        """Get custom CSS for the interface."""
        return """
        .gradio-container {
            max-width: 1200px !important;
        }
        
        .main-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .generate-button {
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4) !important;
            border: none !important;
            color: white !important;
            font-weight: bold !important;
        }
        
        .status-success {
            color: #28a745 !important;
            font-weight: bold !important;
        }
        
        .status-error {
            color: #dc3545 !important;
            font-weight: bold !important;
        }
        
        .tab-nav {
            background: #f8f9fa !important;
        }
        """


def launch_interface(port: int = 7860, share: bool = False):
    """Launch the Gradio interface."""
    interface_app = ReelsBotInterface()
    interface = interface_app.create_interface()
    
    interface.launch(
        server_port=port,
        share=share,
        server_name="0.0.0.0",
        show_api=False
    )


if __name__ == "__main__":
    launch_interface()