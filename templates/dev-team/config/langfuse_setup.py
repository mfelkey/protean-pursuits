"""Langfuse observability setup for CrewAI agents via litellm callbacks."""
import os

def init_langfuse():
    """Enable Langfuse tracing if configured. Call before any CrewAI agent runs."""
    if os.getenv("LANGFUSE_ENABLED", "false").lower() == "true":
        try:
            import litellm
            litellm.success_callback = ["langfuse"]
            litellm.failure_callback = ["langfuse"]
            print("🔭 Langfuse observability enabled")
        except ImportError:
            print("⚠️  litellm not available, Langfuse tracing disabled")
