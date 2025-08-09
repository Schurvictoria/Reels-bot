import asyncio
import json
from typing import Optional, Tuple

import gradio as gr
import httpx
from loguru import logger

from app.core.config import get_settings


class ReelsBotInterface:
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.settings = get_settings()
    
    def create_interface(self) -> gr.Blocks:
        
        with gr.Blocks(
            title="ReelsBot - AI Content Generator",
            theme=gr.themes.Soft(),
            css=self._get_custom_css()
        ) as interface:
            
            gr.HTML("""
                <div style="text-align: center; margin-bottom: 30px;">
                    <h1>🎬 ReelsBot</h1>
                    <p>Make scroll-stopping Reels, Shorts, and TikToks in seconds.</p>
                </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Content")
                    
                    topic = gr.Textbox(
                        label="Topic",
                        placeholder="e.g., '2-minute pasta', 'Morning routine', 'Study hacks'",
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
                        placeholder="Who are we talking to?",
                        lines=2
                    )
                    
                    additional_requirements = gr.Textbox(
                        label="Extras (optional)",
                        placeholder="Visuals, constraints, style — drop it here",
                        lines=3
                    )
                    
                    with gr.Row():
                        include_music = gr.Checkbox(label="Suggest music", value=True)
                    
                    generate_btn = gr.Button("🎬 Generate", variant="primary", size="lg")
                
                with gr.Column(scale=1):
                    gr.Markdown("### Output")
                    
                    status = gr.Textbox(label="Status", interactive=False)
                    
                    with gr.Tabs():
                        with gr.TabItem("📝 Script"):
                            hook_output = gr.Textbox(label="Hook", lines=3, interactive=False)
                            storyline_output = gr.Textbox(label="Storyline", lines=4, interactive=False)
                            script_output = gr.Textbox(label="Complete Script", lines=8, interactive=False)
                        
                        with gr.TabItem("🏷️ Tags & Music"):
                            hashtags_output = gr.Textbox(label="Hashtags", lines=3, interactive=False)
                            music_output = gr.JSON(label="Music Suggestions")
                        
                        with gr.TabItem("⏱️ Timeline"):
                            timestamps_output = gr.JSON(label="Timestamps")
                        
                        with gr.TabItem("📊 Metadata"):
                            metadata_output = gr.JSON(label="Generation Details")
            
            gr.Markdown("### Try these")
            gr.Examples(
                examples=[
                    ["5-minute morning routine", "instagram", "energetic", "Busy professionals", ""],
                    ["How to make perfect pasta", "youtube", "educational", "Cooking beginners", "Show close-up shots"],
                    ["Productivity hacks for students", "tiktok", "trendy", "College students", "Keep it under 30 seconds"],
                    ["Skincare routine for dry skin", "instagram", "calm", "Beauty enthusiasts", "Include product recommendations"]
                ],
                inputs=[topic, platform, tone, target_audience, additional_requirements]
            )
            
            generate_btn.click(
                fn=self.generate_content,
                inputs=[
                    topic, platform, tone, target_audience, 
                    additional_requirements, include_music
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
        include_music: bool
    ) -> Tuple:
        try:
            if not topic.strip():
                return ("❌ Need a topic", "", "", "", "", {}, {}, {})
            
            if not target_audience.strip():
                return ("❌ Who's this for?", "", "", "", "", {}, {}, {})
            
            status = "🔄 Cooking your script..."
            
            request_data = {
                "topic": topic.strip(),
                "platform": platform,
                "tone": tone,
                "target_audience": target_audience.strip(),
                "additional_requirements": additional_requirements.strip() if additional_requirements else None,
                "include_music": include_music
            }
            
            response = asyncio.run(self._make_api_request(request_data))
            
            if response["success"]:
                content = response["content"]
                
                hashtags_formatted = " ".join([f"#{tag}" for tag in content.get("hashtags", [])])
                
                metadata = {
                    "generation_time": response.get("generation_time"),
                    "model_used": content.get("model_used"),
                    "quality_score": content.get("quality_score"),
                    "request_id": response.get("request_id")
                }
                
                return (
                    "✅ All set! Here's your script.",
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
                return (f"❌ {error_msg}", "", "", "", "", {}, {}, {})
        
        except Exception as e:
            logger.error(f"Content generation failed: {str(e)}")
            return (f"❌ {str(e)}", "", "", "", "", {}, {}, {})
    
    async def _make_api_request(self, request_data: dict) -> dict:
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
                    "error": f"Can't reach API: {str(e)}"
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