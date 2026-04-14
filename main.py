"""
AstrBot Plugins Monorepo - Meta Plugin

This meta-plugin loads and manages all sub-plugins in the astrbot-plugins monorepo.
Users can install this single plugin and configure each sub-plugin through the WebUI
with namespaced configuration.
"""

import asyncio
import importlib
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Type

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.provider import LLMResponse, ProviderRequest

logger = logging.getLogger(__name__)


# Sub-plugin registry
SUB_PLUGINS = {
    "langfuse": {
        "module": "packages.langfuse.main",
        "class": "LangfusePlugin",
        "description": "Langfuse integration for LLM observability",
        "version": "1.0.2",
    },
    "discord-forwarder": {
        "module": "packages.discord-forwarder.main",
        "class": "DiscordForwarderPlugin",
        "description": "Discord message forwarding plugin",
        "version": "1.2.1",
    },
    "video-vision": {
        "module": "packages.video-vision.main",
        "class": "VideoVisionPlugin",
        "description": "Video frame extraction for vision models",
        "version": "1.1.0",
    },
}


@register(
    "astrbot-plugins",
    "Minara",
    "AstrBot Plugins Monorepo - Meta plugin that manages all sub-plugins",
    "1.0.0",
)
class AstrBotPluginsMeta(Star):
    """
    Meta plugin that loads and manages all sub-plugins in the monorepo.

    Each sub-plugin is loaded with its own namespaced configuration,
    allowing users to enable/disable and configure each plugin independently
    through the WebUI.
    """

    def __init__(self, context: Context, config: dict) -> None:
        super().__init__(context)
        self.config = config
        self._sub_plugin_instances: Dict[str, Star] = {}
        self._enabled_plugins: set = set()

        # Get list of enabled plugins from config
        enabled_from_config = self.config.get("enabled_plugins", [])
        if isinstance(enabled_from_config, str):
            self._enabled_plugins = {p.strip() for p in enabled_from_config.split(",") if p.strip()}
        elif isinstance(enabled_from_config, list):
            self._enabled_plugins = set(enabled_from_config)
        else:
            # Default: enable all plugins
            self._enabled_plugins = set(SUB_PLUGINS.keys())

        logger.info(f"[AstrBotPlugins] Meta plugin initialized. Enabled plugins: {self._enabled_plugins}")

    async def initialize(self) -> None:
        """Initialize all enabled sub-plugins."""
        logger.info(f"[AstrBotPlugins] Initializing {len(self._enabled_plugins)} sub-plugin(s)...")

        for plugin_name in self._enabled_plugins:
            if plugin_name not in SUB_PLUGINS:
                logger.warning(f"[AstrBotPlugins] Unknown plugin: {plugin_name}")
                continue

            await self._load_sub_plugin(plugin_name)

        logger.info(f"[AstrBotPlugins] All sub-plugins initialized. Active: {list(self._sub_plugin_instances.keys())}")

    async def terminate(self) -> None:
        """Terminate all active sub-plugins."""
        logger.info("[AstrBotPlugins] Terminating all sub-plugins...")

        for plugin_name, instance in list(self._sub_plugin_instances.items()):
            try:
                if hasattr(instance, 'terminate'):
                    await instance.terminate()
                logger.info(f"[AstrBotPlugins] Terminated sub-plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"[AstrBotPlugins] Error terminating {plugin_name}: {e}")

        self._sub_plugin_instances.clear()

    async def _load_sub_plugin(self, plugin_name: str) -> None:
        """Load and initialize a single sub-plugin."""
        plugin_info = SUB_PLUGINS[plugin_name]
        module_path = plugin_info["module"]
        class_name = plugin_info["class"]

        try:
            # Get the plugin root directory (where main.py is located)
            plugin_root = Path(__file__).parent

            # Add the plugin root to Python path if not already there
            str_plugin_root = str(plugin_root)
            if str_plugin_root not in sys.path:
                sys.path.insert(0, str_plugin_root)
                logger.debug(f"[AstrBotPlugins] Added to sys.path: {str_plugin_root}")

            # Import the plugin module
            # module_path is like "packages.langfuse.main"
            module = importlib.import_module(module_path)

            # Get the plugin class
            plugin_class: Type[Star] = getattr(module, class_name)

            # Get namespaced config for this plugin
            plugin_config = self.config.get(plugin_name, {})

            # Create plugin instance
            plugin_instance = plugin_class(self.context, plugin_config)

            # Initialize the plugin
            if hasattr(plugin_instance, 'initialize'):
                await plugin_instance.initialize()

            self._sub_plugin_instances[plugin_name] = plugin_instance

            logger.info(
                f"[AstrBotPlugins] Loaded sub-plugin: {plugin_name} "
                f"(v{plugin_info['version']})"
            )

        except ImportError as e:
            logger.error(f"[AstrBotPlugins] Failed to import {plugin_name}: {e}")
            logger.error(f"[AstrBotPlugins] Module path: {module_path}")
            logger.error(f"[AstrBotPlugins] sys.path: {sys.path}")
        except AttributeError as e:
            logger.error(f"[AstrBotPlugins] Class {class_name} not found in {plugin_name}: {e}")
        except Exception as e:
            logger.error(f"[AstrBotPlugins] Error loading {plugin_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _get_plugin_config(self, plugin_name: str) -> dict:
        """Get the namespaced configuration for a sub-plugin."""
        return self.config.get(plugin_name, {})

    def _get_sub_plugin_instance(self, plugin_name: str) -> Optional[Star]:
        """Get an already loaded sub-plugin instance."""
        return self._sub_plugin_instances.get(plugin_name)

    async def _ensure_sub_plugin_loaded(self, plugin_name: str) -> Optional[Star]:
        """Load a sub-plugin on demand if it is not active yet."""
        instance = self._get_sub_plugin_instance(plugin_name)
        if instance:
            return instance

        if plugin_name not in SUB_PLUGINS:
            return None

        self._enabled_plugins.add(plugin_name)
        await self._load_sub_plugin(plugin_name)
        return self._get_sub_plugin_instance(plugin_name)

    def _delegate_to_plugins(self, method_name: str, *args, **kwargs):
        """
        Delegate a method call to all active sub-plugins that have the method.
        This is used for event handlers.
        """
        logger.info(f"[AstrBotPlugins] _delegate_to_plugins called: method={method_name}, instances={list(self._sub_plugin_instances.keys())}")
        results = []
        for plugin_name, instance in self._sub_plugin_instances.items():
            logger.info(f"[AstrBotPlugins] Checking {plugin_name} for method {method_name}: {hasattr(instance, method_name)}")
            if hasattr(instance, method_name):
                method = getattr(instance, method_name)
                try:
                    # Check if it's a coroutine function
                    if asyncio.iscoroutinefunction(method):
                        results.append(method(*args, **kwargs))
                    else:
                        result = method(*args, **kwargs)
                        results.append(result)
                except Exception as e:
                    logger.error(
                        f"[AstrBotPlugins] Error in {plugin_name}.{method_name}: {e}"
                    )
        logger.info(f"[AstrBotPlugins] Delegation returning {len(results)} results")
        return results

    async def _run_delegated_tasks(self, method_name: str, *args, **kwargs) -> None:
        """Run delegated sub-plugin tasks and swallow per-plugin exceptions."""
        tasks = self._delegate_to_plugins(method_name, *args, **kwargs)
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(
                f"[AstrBotPlugins] Delegation results for {method_name}: {results}"
            )
        else:
            logger.info(
                f"[AstrBotPlugins] No tasks returned from delegation for {method_name}"
            )

    # Event handlers - delegate to sub-plugins

    @filter.platform_adapter_type(filter.PlatformAdapterType.DISCORD)
    async def on_discord_message(self, event: AstrMessageEvent):
        """Handle Discord messages - delegate to sub-plugins."""
        logger.info(f"[AstrBotPlugins] on_discord_message called, delegating to {len(self._sub_plugin_instances)} sub-plugins")
        await self._run_delegated_tasks("on_discord_message", event)

    @filter.on_waiting_llm_request()
    async def on_waiting_llm_request(self, event: AstrMessageEvent):
        """Handle waiting LLM requests - delegate to sub-plugins."""
        logger.info(f"[AstrBotPlugins] on_waiting_llm_request called")
        await self._run_delegated_tasks("on_waiting_llm_request", event)

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """Handle LLM requests - delegate to sub-plugins."""
        await self._run_delegated_tasks("on_llm_request", event, req)

    @filter.on_llm_response()
    async def on_llm_response(self, event: AstrMessageEvent, resp: LLMResponse):
        """Handle LLM responses - delegate to sub-plugins."""
        await self._run_delegated_tasks("on_llm_response", event, resp)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def on_all_messages(self, event: AstrMessageEvent):
        """Handle all messages and fan out to generic or platform-specific sub-plugin listeners."""
        platform_name = event.get_platform_name() if event.platform_meta else ""
        if platform_name:
            await self._run_delegated_tasks(f"on_{platform_name}_message", event)

        await self._run_delegated_tasks("on_all_message", event)

    # Commands

    @filter.command("astrbot_plugins_status")
    async def status_command(self, event: AstrMessageEvent):
        """Show the status of all sub-plugins."""
        status_lines = [
            "**AstrBot Plugins Monorepo Status**",
            f"- Enabled Plugins: {len(self._enabled_plugins)}/{len(SUB_PLUGINS)}",
            "",
            "**Sub-Plugins:**",
        ]

        for plugin_name, info in SUB_PLUGINS.items():
            is_loaded = plugin_name in self._sub_plugin_instances
            is_enabled = plugin_name in self._enabled_plugins
            status = "✓ Loaded" if is_loaded else ("✗ Disabled" if not is_enabled else "✗ Error")
            status_lines.append(f"\n**{plugin_name}** (v{info['version']}): {status}")
            status_lines.append(f"  - {info['description']}")

        yield event.plain_result("\n".join(status_lines))

    @filter.command("astrbot_plugins_enable")
    async def enable_plugin(self, event: AstrMessageEvent):
        """Enable a specific sub-plugin."""
        # Get plugin name from command arguments
        args = event.get_plain_text().split()
        if len(args) < 2:
            yield event.plain_result(
                "Usage: /astrbot_plugins_enable <plugin_name>\n"
                f"Available plugins: {', '.join(SUB_PLUGINS.keys())}"
            )
            return

        plugin_name = args[1]
        if plugin_name not in SUB_PLUGINS:
            yield event.plain_result(f"Unknown plugin: {plugin_name}")
            return

        if plugin_name in self._enabled_plugins:
            yield event.plain_result(f"Plugin '{plugin_name}' is already enabled.")
            return

        # Enable and load the plugin
        self._enabled_plugins.add(plugin_name)
        await self._load_sub_plugin(plugin_name)

        yield event.plain_result(
            f"Plugin '{plugin_name}' has been enabled and loaded.\n"
            f"Note: This change is not persistent. Update the config in WebUI to make it permanent."
        )

    @filter.command("astrbot_plugins_disable")
    async def disable_plugin(self, event: AstrMessageEvent):
        """Disable a specific sub-plugin."""
        # Get plugin name from command arguments
        args = event.get_plain_text().split()
        if len(args) < 2:
            yield event.plain_result(
                "Usage: /astrbot_plugins_disable <plugin_name>\n"
                f"Available plugins: {', '.join(SUB_PLUGINS.keys())}"
            )
            return

        plugin_name = args[1]
        if plugin_name not in SUB_PLUGINS:
            yield event.plain_result(f"Unknown plugin: {plugin_name}")
            return

        if plugin_name not in self._enabled_plugins:
            yield event.plain_result(f"Plugin '{plugin_name}' is already disabled.")
            return

        # Disable and unload the plugin
        self._enabled_plugins.discard(plugin_name)

        if plugin_name in self._sub_plugin_instances:
            instance = self._sub_plugin_instances.pop(plugin_name)
            if hasattr(instance, 'terminate'):
                await instance.terminate()

        yield event.plain_result(
            f"Plugin '{plugin_name}' has been disabled and unloaded.\n"
            f"Note: This change is not persistent. Update the config in WebUI to make it permanent."
        )

    @filter.command("video_vision_status")
    async def video_vision_status_command(self, event: AstrMessageEvent):
        """Show the Video Vision sub-plugin status."""
        instance = self._get_sub_plugin_instance("video-vision")
        if not instance or not hasattr(instance, "get_status_text"):
            yield event.plain_result(
                "Video Vision plugin is not currently loaded.\n"
                "Use `/astrbot_plugins_enable video-vision` to load it first."
            )
            return

        yield event.plain_result(instance.get_status_text())

    @filter.command("video_vision_enable")
    async def video_vision_enable_command(self, event: AstrMessageEvent):
        """Enable the Video Vision sub-plugin."""
        instance = await self._ensure_sub_plugin_loaded("video-vision")
        if not instance or not hasattr(instance, "enable_plugin"):
            yield event.plain_result("Failed to load the Video Vision plugin.")
            return

        instance.enable_plugin()
        yield event.plain_result(
            "Video Vision plugin enabled.\n"
            "Note: This change is not persistent. Update the config in WebUI to make it permanent."
        )

    @filter.command("video_vision_disable")
    async def video_vision_disable_command(self, event: AstrMessageEvent):
        """Disable the Video Vision sub-plugin."""
        instance = self._get_sub_plugin_instance("video-vision")
        if not instance or not hasattr(instance, "disable_plugin"):
            yield event.plain_result("Video Vision plugin is already disabled.")
            return

        instance.disable_plugin()
        yield event.plain_result(
            "Video Vision plugin disabled.\n"
            "Note: This change is not persistent. Update the config in WebUI to make it permanent."
        )
