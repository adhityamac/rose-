"""
Plugin System for Rose AI Assistant
Extensible architecture for adding new features
"""

import os
import sys
import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class PluginType(Enum):
    VOICE_COMMAND = "voice_command"
    UI_WIDGET = "ui_widget"
    MEDIA_HANDLER = "media_handler"
    AI_SERVICE = "ai_service"
    SYSTEM_UTILITY = "system_utility"
    BACKGROUND_TASK = "background_task"

@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    enabled: bool = True

class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if plugin is available"""
        pass

class VoiceCommandPlugin(PluginInterface):
    """Base class for voice command plugins"""
    
    @abstractmethod
    def get_commands(self) -> Dict[str, Callable]:
        """Get voice commands provided by this plugin"""
        pass
    
    @abstractmethod
    def get_command_patterns(self) -> Dict[str, str]:
        """Get command patterns for voice recognition"""
        pass

class UIWidgetPlugin(PluginInterface):
    """Base class for UI widget plugins"""
    
    @abstractmethod
    def create_widget(self, parent) -> Any:
        """Create the UI widget"""
        pass
    
    @abstractmethod
    def get_widget_name(self) -> str:
        """Get widget display name"""
        pass

class MediaHandlerPlugin(PluginInterface):
    """Base class for media handler plugins"""
    
    @abstractmethod
    def can_handle(self, media_type: str) -> bool:
        """Check if plugin can handle media type"""
        pass
    
    @abstractmethod
    def handle_media(self, media_data: Any) -> bool:
        """Handle media data"""
        pass

class PluginManager:
    """Manages plugins and their lifecycle"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.plugin_directories = ["plugins", "extensions"]
        self.loaded_plugins: List[str] = []
        
        # Create plugin directories if they don't exist
        for directory in self.plugin_directories:
            os.makedirs(directory, exist_ok=True)
    
    def load_plugins(self) -> int:
        """Load all available plugins"""
        loaded_count = 0
        
        for directory in self.plugin_directories:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    if filename.endswith('.py') and not filename.startswith('_'):
                        plugin_name = filename[:-3]
                        if self.load_plugin(plugin_name, directory):
                            loaded_count += 1
        
        return loaded_count
    
    def load_plugin(self, plugin_name: str, directory: str = "plugins") -> bool:
        """Load a specific plugin"""
        try:
            # Add directory to Python path
            plugin_path = os.path.join(directory, f"{plugin_name}.py")
            if not os.path.exists(plugin_path):
                return False
            
            # Import the plugin module
            spec = importlib.util.spec_from_file_location(plugin_name, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find plugin classes
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj != PluginInterface):
                    plugin_classes.append(obj)
            
            # Initialize plugins
            for plugin_class in plugin_classes:
                plugin_instance = plugin_class()
                plugin_info = plugin_instance.get_info()
                
                if plugin_instance.is_available() and plugin_instance.initialize():
                    self.plugins[plugin_name] = plugin_instance
                    self.plugin_info[plugin_name] = plugin_info
                    self.loaded_plugins.append(plugin_name)
                    print(f"✅ Loaded plugin: {plugin_info.name} v{plugin_info.version}")
                    return True
                else:
                    print(f"❌ Failed to load plugin: {plugin_name}")
                    return False
            
            return False
            
        except Exception as e:
            print(f"❌ Error loading plugin {plugin_name}: {e}")
            return False
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self.plugins:
            try:
                self.plugins[plugin_name].cleanup()
                del self.plugins[plugin_name]
                if plugin_name in self.plugin_info:
                    del self.plugin_info[plugin_name]
                if plugin_name in self.loaded_plugins:
                    self.loaded_plugins.remove(plugin_name)
                print(f"✅ Unloaded plugin: {plugin_name}")
                return True
            except Exception as e:
                print(f"❌ Error unloading plugin {plugin_name}: {e}")
                return False
        return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a plugin by name"""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[PluginInterface]:
        """Get plugins by type"""
        return [plugin for plugin in self.plugins.values() 
                if plugin.get_info().plugin_type == plugin_type]
    
    def get_voice_commands(self) -> Dict[str, Callable]:
        """Get all voice commands from plugins"""
        commands = {}
        for plugin in self.get_plugins_by_type(PluginType.VOICE_COMMAND):
            if isinstance(plugin, VoiceCommandPlugin):
                commands.update(plugin.get_commands())
        return commands
    
    def get_command_patterns(self) -> Dict[str, str]:
        """Get all command patterns from plugins"""
        patterns = {}
        for plugin in self.get_plugins_by_type(PluginType.VOICE_COMMAND):
            if isinstance(plugin, VoiceCommandPlugin):
                patterns.update(plugin.get_command_patterns())
        return patterns
    
    def get_ui_widgets(self) -> Dict[str, Callable]:
        """Get UI widget creators from plugins"""
        widgets = {}
        for plugin in self.get_plugins_by_type(PluginType.UI_WIDGET):
            if isinstance(plugin, UIWidgetPlugin):
                widgets[plugin.get_widget_name()] = plugin.create_widget
        return widgets
    
    def get_media_handlers(self) -> List[MediaHandlerPlugin]:
        """Get media handler plugins"""
        return [plugin for plugin in self.get_plugins_by_type(PluginType.MEDIA_HANDLER)
                if isinstance(plugin, MediaHandlerPlugin)]
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        if plugin_name in self.plugin_info:
            self.plugin_info[plugin_name].enabled = True
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        if plugin_name in self.plugin_info:
            self.plugin_info[plugin_name].enabled = False
            return True
        return False
    
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins"""
        status = {}
        for name, info in self.plugin_info.items():
            plugin = self.plugins.get(name)
            status[name] = {
                "name": info.name,
                "version": info.version,
                "enabled": info.enabled,
                "loaded": name in self.loaded_plugins,
                "available": plugin.is_available() if plugin else False,
                "type": info.plugin_type.value
            }
        return status
    
    def cleanup_all(self):
        """Cleanup all plugins"""
        for plugin in self.plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"Error cleaning up plugin: {e}")
        
        self.plugins.clear()
        self.plugin_info.clear()
        self.loaded_plugins.clear()

# Global instance
plugin_manager = PluginManager()

# Example plugin template
class ExampleVoiceCommandPlugin(VoiceCommandPlugin):
    """Example voice command plugin"""
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            name="Example Voice Commands",
            version="1.0.0",
            description="Example voice command plugin",
            author="Rose AI",
            plugin_type=PluginType.VOICE_COMMAND,
            dependencies=[]
        )
    
    def initialize(self) -> bool:
        return True
    
    def cleanup(self) -> None:
        pass
    
    def is_available(self) -> bool:
        return True
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "example_command": self._handle_example
        }
    
    def get_command_patterns(self) -> Dict[str, str]:
        return {
            "example_command": "example|test|demo"
        }
    
    def _handle_example(self, text: str):
        print("🎉 Example command executed!")
