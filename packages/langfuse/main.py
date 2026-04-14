"""
AstrBot Langfuse Integration Plugin

This plugin integrates Langfuse LLM observability with AstrBot,
enabling tracing of LLM calls and message events.
"""

import asyncio
import base64
import logging
import os
import sys
import time
import traceback
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from astrbot.api import logger as astrbot_logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.provider import LLMResponse, ProviderRequest
from astrbot.api.star import Context, Star

# Import shared context variable for inter-plugin communication
from packages.shared import langfuse_observation_ctx

def setup_debug_logger(config: dict):
    """Setup a debug logger that writes to a file"""
    debug_logger = logging.getLogger("langfuse_plugin")
    debug_logger.setLevel(logging.DEBUG)
    debug_logger.handlers = []

    # Get log file path from config or use default
    debug_log_file = config.get("debug_log_file", "/tmp/astrbot_langfuse_debug.log")

    try:
        file_handler = logging.FileHandler(debug_log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        debug_logger.addHandler(file_handler)
    except Exception:
        pass
    return debug_logger, debug_log_file

# Module-level debug logger, will be properly initialized in __init__
debug_log = None

def log_both(level, msg):
    """Log to both AstrBot logger and debug file"""
    try:
        if level == "DEBUG":
            astrbot_logger.debug(f"[Langfuse] {msg}")
        elif level == "INFO":
            astrbot_logger.info(f"[Langfuse] {msg}")
        elif level == "WARNING":
            astrbot_logger.warning(f"[Langfuse] {msg}")
        elif level == "ERROR":
            astrbot_logger.error(f"[Langfuse] {msg}")

        # Also log to debug file if available
        if debug_log is not None:
            debug_log.log(getattr(logging, level, logging.INFO), msg)
    except Exception:
        pass

# Lazy import
Langfuse = None
propagate_attributes = None
LANGFUSE_AVAILABLE = False

def _ensure_langfuse_imported():
    """Lazily import langfuse package."""
    global Langfuse, propagate_attributes, LANGFUSE_AVAILABLE

    if LANGFUSE_AVAILABLE:
        return True

    try:
        from langfuse import Langfuse as _Langfuse
        from langfuse._client.propagation import propagate_attributes as _propagate_attributes
        Langfuse = _Langfuse
        propagate_attributes = _propagate_attributes
        LANGFUSE_AVAILABLE = True
        log_both("INFO", "langfuse package imported successfully")
        return True
    except ImportError as e:
        log_both("ERROR", f"langfuse package not available: {e}")
        return False


# Helper functions for image encoding (matching AstrBot's behavior)
async def _download_image_by_url(url: str) -> str:
    """Download image from URL to temp file."""
    import tempfile
    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    log_both("WARNING", f"Failed to download image: HTTP {resp.status}")
                    return ""
                content = await resp.read()

        # Create temp file with appropriate extension
        suffix = ".jpg"
        if ".png" in url.lower():
            suffix = ".png"
        elif ".webp" in url.lower():
            suffix = ".webp"
        elif ".gif" in url.lower():
            suffix = ".gif"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(content)
            return f.name
    except Exception as e:
        log_both("WARNING", f"Failed to download image: {e}")
        return ""


async def _encode_image_bs64(image_path: str) -> str:
    """Convert image to base64 data URL (matching AstrBot's behavior)."""
    if image_path.startswith("base64://"):
        return image_path.replace("base64://", "data:image/jpeg;base64,")

    if image_path.startswith("data:"):
        return image_path

    try:
        with open(image_path, "rb") as f:
            image_bs64 = base64.b64encode(f.read()).decode("utf-8")

        # Detect image type
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/jpeg"
        if ext == ".png":
            mime_type = "image/png"
        elif ext == ".webp":
            mime_type = "image/webp"
        elif ext == ".gif":
            mime_type = "image/gif"

        return f"data:{mime_type};base64,{image_bs64}"
    except Exception as e:
        log_both("WARNING", f"Failed to encode image: {e}")
        return ""


@dataclass
class SessionInfo:
    """Session information for tracking conversations"""
    session_id: str
    trace_id: str
    last_activity: float
    current_observation: Optional[object] = None
    metadata: dict = field(default_factory=dict)


class LangfusePlugin(Star):
    """Langfuse integration plugin for AstrBot"""

    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)

        self.plugin_config = config or {}
        self.langfuse_client = None
        self.enabled = False
        self.sessions: dict[str, SessionInfo] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

        # Setup debug logger with config
        global debug_log
        debug_log, self.debug_log_file = setup_debug_logger(self.plugin_config)

        log_both("INFO", "=" * 60)
        log_both("INFO", "MODULE LOADED - astrbot_plugin_langfuse")
        log_both("INFO", f"Python version: {sys.version}")
        log_both("INFO", f"Debug log file: {self.debug_log_file}")
        log_both("INFO", "=" * 60)
        log_both("INFO", f"Config keys: {list(self.plugin_config.keys())}")

    async def initialize(self) -> None:
        """Called when plugin is activated."""
        if not _ensure_langfuse_imported():
            return

        if not self.plugin_config.get("enabled", True):
            log_both("INFO", "Plugin is DISABLED in config")
            return

        secret_key = self.plugin_config.get("secret_key", "")
        public_key = self.plugin_config.get("public_key", "")
        base_url = self.plugin_config.get("base_url", "https://cloud.langfuse.com")

        if not secret_key or not public_key:
            log_both("ERROR", "SECRET_KEY or PUBLIC_KEY is empty")
            return

        try:
            self.langfuse_client = Langfuse(
                secret_key=secret_key,
                public_key=public_key,
                host=base_url,
            )
            self.enabled = True

            try:
                self.langfuse_client.auth_check()
                log_both("INFO", "Auth check PASSED - Langfuse connected!")
            except Exception as e:
                log_both("WARNING", f"Auth check failed: {e}")

            self._cleanup_task = asyncio.create_task(self._cleanup_sessions())
            log_both("INFO", "Plugin initialized successfully")

        except Exception as e:
            log_both("ERROR", f"Failed to create Langfuse client: {e}")

    async def terminate(self) -> None:
        """Called when plugin is disabled or reloaded."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.langfuse_client:
            try:
                self.langfuse_client.flush()
            except Exception:
                pass

    def _get_or_create_session(self, user_id: str, platform: str) -> SessionInfo:
        """Get or create a session for a user"""
        session_key = f"{platform}:{user_id}"
        current_time = time.time()
        session_timeout = self.plugin_config.get("session_timeout", 3600)

        if session_key in self.sessions:
            session = self.sessions[session_key]
            if current_time - session.last_activity > session_timeout:
                session = SessionInfo(
                    session_id=str(uuid.uuid4()),
                    trace_id=str(uuid.uuid4()),
                    last_activity=current_time,
                    metadata={"platform": platform, "user_id": user_id},
                )
                self.sessions[session_key] = session
            else:
                session.last_activity = current_time
        else:
            session = SessionInfo(
                session_id=str(uuid.uuid4()),
                trace_id=str(uuid.uuid4()),
                last_activity=current_time,
                metadata={"platform": platform, "user_id": user_id},
            )
            self.sessions[session_key] = session

        return session

    async def _cleanup_sessions(self):
        """Periodically cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)
                current_time = time.time()
                session_timeout = self.plugin_config.get("session_timeout", 3600)

                expired_keys = [
                    key for key, session in self.sessions.items()
                    if current_time - session.last_activity > session_timeout
                ]

                for key in expired_keys:
                    del self.sessions[key]

                if self.langfuse_client:
                    self.langfuse_client.flush()

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    @filter.command("langfuse_status")
    async def langfuse_status(self, event: AstrMessageEvent):
        """Check Langfuse connection status"""
        if not self.enabled:
            yield event.plain_result(
                f"Langfuse not enabled.\n"
                f"Check logs: {self.debug_log_file}"
            )
            return

        base_url = self.plugin_config.get("base_url", "https://cloud.langfuse.com")
        status_msg = (
            f"Langfuse Status:\n"
            f"- Status: Enabled\n"
            f"- Base URL: {base_url}\n"
            f"- Active Sessions: {len(self.sessions)}\n"
            f"- Debug Log: {self.debug_log_file}"
        )
        yield event.plain_result(status_msg)

    @filter.command("langfuse_flush")
    async def langfuse_flush(self, event: AstrMessageEvent):
        """Manually flush Langfuse traces"""
        if not self.enabled or not self.langfuse_client:
            yield event.plain_result("Langfuse not enabled.")
            return

        try:
            self.langfuse_client.flush()
            yield event.plain_result("Traces flushed.")
        except Exception as e:
            yield event.plain_result(f"Flush failed: {e}")

    async def on_all_message(self, event: AstrMessageEvent):
        """
        Handle all message events for tracing.
        Note: This is called from the meta-plugin's on_all_messages handler.
        """
        if not self.enabled or not self.plugin_config.get("enabled_message_tracing", True):
            return

        if not self.langfuse_client:
            return

        try:
            user_id = event.unified_msg_origin
            platform = event.get_platform_name() if hasattr(event, "get_platform_name") else "unknown"
            session = self._get_or_create_session(user_id, platform)
            message_content = event.message_str or ""
            environment = self.plugin_config.get("environment", "production")

            # Use propagate_attributes to properly set session_id and user_id
            # This ensures all observations inherit these trace-level attributes
            with propagate_attributes(
                session_id=session.session_id,
                user_id=user_id,
                metadata={
                    "environment": environment,
                    "platform": platform,
                },
            ):
                observation = self.langfuse_client.start_observation(
                    name="user_message",
                    as_type="span",
                    input={"content": message_content},
                )
                observation.end()

        except Exception as e:
            log_both("ERROR", f"Message trace error: {e}")

    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """Hook into LLM request for tracing"""
        if not self.enabled or not self.plugin_config.get("enabled_llm_tracing", True):
            return

        if not self.langfuse_client:
            return

        try:
            user_id = event.unified_msg_origin
            platform = event.get_platform_name() if hasattr(event, "get_platform_name") else "unknown"
            session = self._get_or_create_session(user_id, platform)
            environment = self.plugin_config.get("environment", "production")

            # Build input data in ChatML format for Langfuse playground compatibility
            # ChatML format: [{"role": "system/user/assistant", "content": "..."}]
            chatml_messages = []
            observation_metadata = {}

            # Add system prompt if present
            if req.system_prompt:
                chatml_messages.append({"role": "system", "content": req.system_prompt})

            # Add conversation context (already in OpenAI/ChatML format)
            # Include ALL contexts to match what AstrBot actually sends
            if req.contexts:
                for ctx in req.contexts:
                    if isinstance(ctx, dict) and "role" in ctx and "content" in ctx:
                        chatml_messages.append({"role": ctx["role"], "content": ctx["content"]})

            # Build current user message content
            user_content = req.prompt or ""

            # Add extra content parts (like VideoVision analysis) to user message
            if req.extra_user_content_parts:
                extra_text_parts = []
                for part in req.extra_user_content_parts:
                    part_text = ""
                    if hasattr(part, 'text'):
                        part_text = part.text
                    elif hasattr(part, 'model_dump'):
                        part_dict = part.model_dump()
                        part_text = part_dict.get("text", "")
                    elif isinstance(part, dict):
                        part_text = part.get("text", "")

                    if part_text:
                        extra_text_parts.append(part_text)

                    # Log if video vision analysis is detected
                    if "[Video Content Analysis]" in part_text:
                        log_both("INFO", f"VideoVision analysis detected in LLM input ({len(part_text)} chars)")
                        observation_metadata["has_video_analysis"] = True

                if extra_text_parts:
                    if user_content:
                        user_content = f"{user_content}\n\n" + "\n\n".join(extra_text_parts)
                    else:
                        user_content = "\n\n".join(extra_text_parts)

            # Add current user message
            if user_content or req.image_urls:
                # Handle image URLs as multimodal content
                if req.image_urls:
                    content_parts = [{"type": "text", "text": user_content}] if user_content else []
                    for img_url in req.image_urls:
                        # Convert image to base64 like AstrBot does
                        try:
                            if img_url.startswith("http"):
                                # Download and encode
                                image_path = await _download_image_by_url(img_url)
                                if image_path:
                                    image_data = await _encode_image_bs64(image_path)
                                    # Clean up temp file
                                    try:
                                        os.unlink(image_path)
                                    except Exception:
                                        pass
                                else:
                                    image_data = ""
                            elif img_url.startswith("file:///"):
                                image_path = img_url.replace("file:///", "")
                                image_data = await _encode_image_bs64(image_path)
                            else:
                                image_data = await _encode_image_bs64(img_url)

                            if image_data:
                                content_parts.append({"type": "image_url", "image_url": {"url": image_data}})
                        except Exception as e:
                            log_both("WARNING", f"Failed to process image {img_url}: {e}")
                    chatml_messages.append({"role": "user", "content": content_parts})
                else:
                    chatml_messages.append({"role": "user", "content": user_content})

            # Add tool call results to match what AstrBot sends
            if req.tool_calls_result:
                observation_metadata["has_tool_results"] = True
                log_both("INFO", "Tool call results detected in request")
                try:
                    # Import ToolCallsResult type for type checking
                    if hasattr(req.tool_calls_result, 'to_openai_messages'):
                        # Single ToolCallsResult
                        tool_messages = req.tool_calls_result.to_openai_messages()
                        chatml_messages.extend(tool_messages)
                        log_both("DEBUG", f"Added {len(tool_messages)} tool result messages")
                    elif isinstance(req.tool_calls_result, list):
                        # List of ToolCallsResult
                        for tcr in req.tool_calls_result:
                            if hasattr(tcr, 'to_openai_messages'):
                                tool_messages = tcr.to_openai_messages()
                                chatml_messages.extend(tool_messages)
                                log_both("DEBUG", f"Added {len(tool_messages)} tool result messages from list")
                except Exception as e:
                    log_both("WARNING", f"Failed to add tool call results to trace: {e}")

            # Use ChatML messages as input for playground compatibility
            input_data = chatml_messages

            # Get model name
            model = req.model or "unknown"

            # Store model in session for use in response
            session.metadata["model"] = model
            session.metadata["prompt"] = req.prompt

            # Determine observation name based on context variable or content
            observation_name = "llm_generation"

            # Check if a plugin has set observation metadata via context variable
            ctx_observation = langfuse_observation_ctx.get(None)
            if ctx_observation:
                observation_name = ctx_observation.get("name", "llm_generation")
                # Merge context metadata with existing observation_metadata
                ctx_metadata = ctx_observation.get("metadata", {})
                observation_metadata.update(ctx_metadata)
                log_both("INFO", f"Using custom observation name from context: {observation_name}")
            else:
                # Fallback: check if video analysis was injected into this request (main conversation)
                if req.extra_user_content_parts:
                    for part in req.extra_user_content_parts:
                        part_text = ""
                        if hasattr(part, 'text'):
                            part_text = part.text
                        elif hasattr(part, 'model_dump'):
                            part_dict = part.model_dump()
                            part_text = part_dict.get("text", "")
                        elif isinstance(part, dict):
                            part_text = part.get("text", "")

                        if "[Video Content Analysis]" in part_text:
                            observation_name = "Main Conversation (with VideoVision)"
                            observation_metadata["has_video_analysis"] = True
                            break

            # Store observation name in session for use in response
            session.metadata["observation_name"] = observation_name
            session.metadata["has_tool_results"] = observation_metadata.get("has_tool_results", False)

            # Use propagate_attributes to properly set session_id and user_id
            with propagate_attributes(
                session_id=session.session_id,
                user_id=user_id,
                metadata={
                    "environment": environment,
                    "platform": platform,
                    **observation_metadata,
                },
            ):
                # Create a generation observation (will be updated in response)
                observation = self.langfuse_client.start_observation(
                    name=observation_name,
                    as_type="generation",
                    model=model,
                    input=input_data,
                )

                # Store observation in session for later update
                session.current_observation = observation
                session.metadata["observation_id"] = observation.observation_id if hasattr(observation, 'observation_id') else None

            log_both("INFO", f"LLM request traced - model: {model}")

        except Exception as e:
            log_both("ERROR", f"LLM request trace error: {e}")
            log_both("ERROR", traceback.format_exc())

    async def on_llm_response(self, event: AstrMessageEvent, resp: LLMResponse):
        """Hook into LLM response for tracing"""
        if not self.enabled or not self.plugin_config.get("enabled_llm_tracing", True):
            return

        if not self.langfuse_client:
            return

        try:
            user_id = event.unified_msg_origin
            platform = event.get_platform_name() if hasattr(event, "get_platform_name") else "unknown"
            session = self._get_or_create_session(user_id, platform)
            environment = self.plugin_config.get("environment", "production")

            # Get completion text
            completion_text = ""
            if resp.completion_text:
                completion_text = resp.completion_text
            elif resp.result_chain:
                completion_text = resp.result_chain.get_plain_text() if hasattr(resp.result_chain, 'get_plain_text') else str(resp.result_chain)

            # Build output in ChatML format
            # Check for tool calls in response
            output_data = completion_text
            has_tool_calls = False

            if hasattr(resp, 'tools_call_args') and resp.tools_call_args:
                has_tool_calls = True
                # Build ChatML format output with tool calls
                tool_calls = []
                for i, (call_id, name, args) in enumerate(zip(
                    resp.tools_call_ids or [],
                    resp.tools_call_name or [],
                    resp.tools_call_args or []
                )):
                    tool_calls.append({
                        "id": call_id or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": args if isinstance(args, str) else str(args)
                        }
                    })

                output_data = {
                    "role": "assistant",
                    "content": completion_text if completion_text else None,
                    "tool_calls": tool_calls
                }
                log_both("INFO", f"Response includes {len(tool_calls)} tool calls")

            # Also check for tool call results in request (tool responses)
            if session.metadata.get("has_tool_results"):
                has_tool_calls = True

            # Get model name - try multiple sources
            model = session.metadata.get("model", "unknown")

            # Try to get model from raw_completion
            if resp.raw_completion and hasattr(resp.raw_completion, 'model'):
                model = resp.raw_completion.model

            # Get usage info
            usage_dict = None
            if resp.usage:
                usage_dict = {
                    "input": resp.usage.input if hasattr(resp.usage, 'input') else 0,
                    "output": resp.usage.output if hasattr(resp.usage, 'output') else 0,
                    "total": resp.usage.total if hasattr(resp.usage, 'total') else 0,
                }

            # Check if we have a pending observation from request
            if session.current_observation:
                # Update the existing observation (already has session_id and user_id from request)
                session.current_observation.update(
                    output=output_data,
                    model=model,
                )

                # Log custom observation name if used
                obs_name = session.metadata.get("observation_name", "llm_generation")
                if obs_name != "llm_generation":
                    log_both("INFO", f"Custom observation '{obs_name}' completed")

                if usage_dict:
                    session.current_observation.update(usage=usage_dict)

                session.current_observation.end()
                session.current_observation = None
            else:
                # Create a new generation observation with propagate_attributes
                # Build ChatML format input from session metadata
                chatml_input = []
                prompt = session.metadata.get("prompt", "")
                if prompt:
                    chatml_input.append({"role": "user", "content": prompt})

                with propagate_attributes(
                    session_id=session.session_id,
                    user_id=user_id,
                    metadata={
                        "environment": environment,
                        "platform": platform,
                    },
                ):
                    generation = self.langfuse_client.start_observation(
                        name="llm_generation",
                        as_type="generation",
                        model=model,
                        input=chatml_input,
                        output=output_data,
                    )

                    if usage_dict:
                        generation.update(usage=usage_dict)

                    generation.end()

            # Flush to ensure data is sent
            self.langfuse_client.flush()

            log_both("INFO", f"LLM response traced - model: {model}, tokens: {usage_dict}")

        except Exception as e:
            log_both("ERROR", f"LLM response trace error: {e}")
            log_both("ERROR", traceback.format_exc())
