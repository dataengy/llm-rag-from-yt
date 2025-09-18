"""Gradio web interface for RAG pipeline."""

from typing import Optional

import gradio as gr
from loguru import logger

from ..pipeline import RAGPipeline


class GradioRAGApp:
    """Gradio application for RAG pipeline."""

    def __init__(self):
        """Initialize Gradio app."""
        self.pipeline: Optional[RAGPipeline] = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize the RAG pipeline."""
        try:
            self.pipeline = RAGPipeline()
            logger.info("Pipeline initialized for Gradio app")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            self.pipeline = None

    def process_youtube_url(
        self, url: str, use_fake_asr: bool = True, language: str = "ru"
    ) -> tuple[str, str]:
        """Process a single YouTube URL.

        Args:
            url: YouTube URL to process
            use_fake_asr: Whether to use fake ASR
            language: Language for transcription

        Returns:
            Tuple of (status_message, detailed_info)
        """
        if not self.pipeline:
            return "❌ Pipeline not initialized", "Check server logs for errors"

        if not url.strip():
            return "❌ Please provide a YouTube URL", ""

        try:
            # Update config
            self.pipeline.config.use_fake_asr = use_fake_asr

            # Reinitialize transcriber with new settings
            self.pipeline.transcriber = self.pipeline.transcriber.__class__(
                model_name=self.pipeline.config.asr_model,
                device=self.pipeline.config.device,
                compute_type=self.pipeline.config.whisper_precision,
            )

            results = self.pipeline.download_and_process([url])

            if not results.get("downloads"):
                return "❌ Failed to download video", "Check URL and try again"

            downloads = results["downloads"]
            transcriptions = len(results.get("transcriptions", {}))
            chunks = results.get("chunks", 0)

            status_msg = f"✅ Successfully processed!\n📥 Downloads: {len(downloads)}\n📝 Transcriptions: {transcriptions}\n📦 Chunks: {chunks}"

            detail_info = ""
            for url_key, download_info in downloads.items():
                detail_info += f"Title: {download_info.get('title', 'Unknown')}\n"
                detail_info += f"Duration: {download_info.get('duration', 0)}s\n"
                detail_info += f"File: {download_info.get('file_path', 'N/A')}\n\n"

            return status_msg, detail_info

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return f"❌ Error: {str(e)}", "Check server logs for details"

    def query_system(self, question: str, top_k: int = 3) -> tuple[str, str]:
        """Query the RAG system.

        Args:
            question: Question to ask
            top_k: Number of top results

        Returns:
            Tuple of (answer, sources_info)
        """
        if not self.pipeline:
            return "❌ Pipeline not initialized", ""

        if not question.strip():
            return "❌ Please provide a question", ""

        try:
            result = self.pipeline.query(question, top_k)

            answer = result["answer"]
            sources = result["sources"]

            sources_info = "📚 Sources:\n"
            for i, source in enumerate(sources, 1):
                source_id = source.get("metadata", {}).get("source_id", "unknown")
                distance = source.get("distance", 0)
                sources_info += f"{i}. {source_id} (similarity: {1 - distance:.3f})\n"
                sources_info += f"   {source['text'][:100]}...\n\n"

            return answer, sources_info

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return f"❌ Error: {str(e)}", "Check server logs for details"

    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface."""
        with gr.Blocks(
            title="LLM RAG YouTube Audio Processing",
            theme=gr.themes.Soft(),
        ) as interface:
            gr.Markdown("# 🎵 LLM RAG YouTube Audio Processing")
            gr.Markdown("Process YouTube audio content and ask questions using RAG")

            with gr.Tab("📥 Process Audio"):
                gr.Markdown("## Download and Process YouTube Audio")

                with gr.Row():
                    with gr.Column():
                        url_input = gr.Textbox(
                            label="YouTube URL",
                            placeholder="https://www.youtube.com/watch?v=...",
                            lines=1,
                        )
                        language_input = gr.Dropdown(
                            choices=["ru", "en", "auto"],
                            value="ru",
                            label="Language",
                        )
                        fake_asr_checkbox = gr.Checkbox(
                            label="Use Fake ASR (for testing)",
                            value=True,
                        )
                        process_btn = gr.Button("🔄 Process", variant="primary")

                    with gr.Column():
                        process_status = gr.Textbox(
                            label="Status",
                            lines=5,
                            interactive=False,
                        )
                        process_details = gr.Textbox(
                            label="Details",
                            lines=5,
                            interactive=False,
                        )

                process_btn.click(
                    fn=self.process_youtube_url,
                    inputs=[url_input, fake_asr_checkbox, language_input],
                    outputs=[process_status, process_details],
                )

            with gr.Tab("❓ Ask Questions"):
                gr.Markdown("## Query the RAG System")

                with gr.Row():
                    with gr.Column():
                        question_input = gr.Textbox(
                            label="Your Question",
                            placeholder="Задайте вопрос о содержании аудио...",
                            lines=2,
                        )
                        top_k_slider = gr.Slider(
                            minimum=1,
                            maximum=10,
                            value=3,
                            step=1,
                            label="Number of Sources",
                        )
                        query_btn = gr.Button("🔍 Ask", variant="primary")

                    with gr.Column():
                        answer_output = gr.Textbox(
                            label="Answer",
                            lines=5,
                            interactive=False,
                        )
                        sources_output = gr.Textbox(
                            label="Sources",
                            lines=8,
                            interactive=False,
                        )

                query_btn.click(
                    fn=self.query_system,
                    inputs=[question_input, top_k_slider],
                    outputs=[answer_output, sources_output],
                )

            with gr.Tab("📊 Status"):
                gr.Markdown("## System Status")

                status_btn = gr.Button("🔄 Refresh Status")
                status_output = gr.JSON(label="Pipeline Status")

                def get_pipeline_status():
                    if not self.pipeline:
                        return {"error": "Pipeline not initialized"}
                    try:
                        return self.pipeline.get_status()
                    except Exception as e:
                        return {"error": str(e)}

                status_btn.click(
                    fn=get_pipeline_status,
                    outputs=[status_output],
                )

        return interface

    def launch(self, **kwargs):
        """Launch the Gradio interface."""
        interface = self.create_interface()
        return interface.launch(**kwargs)


def create_app() -> GradioRAGApp:
    """Create Gradio RAG application."""
    return GradioRAGApp()


if __name__ == "__main__":
    app = create_app()
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
