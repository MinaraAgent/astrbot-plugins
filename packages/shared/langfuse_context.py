"""
Shared Langfuse context variable for inter-plugin communication.

Plugins can set this before LLM calls to customize Langfuse observation names.
"""
from contextvars import ContextVar
from typing import Optional

# Context variable for passing metadata through the call chain
langfuse_observation_ctx: ContextVar[Optional[dict]] = ContextVar('langfuse_observation')
