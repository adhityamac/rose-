"""
Theme Manager for Rose AI Assistant
Multiple UI themes and styles with fast switching
"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum

class ThemeType(Enum):
    DARK = "dark"
    LIGHT = "light"
    NEON = "neon"
    MINIMAL = "minimal"
    COSMIC = "cosmic"
    OCEAN = "ocean"

@dataclass
class ColorScheme:
    """Color scheme for a theme"""
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    text_secondary: str
    border: str
    success: str
    warning: str
    error: str
    info: str

@dataclass
class Theme:
    """Complete theme definition"""
    name: str
    type: ThemeType
    colors: ColorScheme
    font_family: str
    font_size: int
    border_radius: int
    shadow: str
    animation_speed: int

class ThemeManager:
    """Manages themes and styling"""
    
    def __init__(self):
        self.current_theme: Theme = None
        self.themes: Dict[str, Theme] = {}
        self._setup_default_themes()
        self.set_theme("cosmic")  # Default theme
    
    def _setup_default_themes(self):
        """Setup default themes"""
        
        # Cosmic Theme (Default)
        cosmic_colors = ColorScheme(
            primary="#FF69B4",
            secondary="#9932CC",
            accent="#FFB6C1",
            background="linear-gradient(135deg, #FF69B4, #9932CC, #FFB6C1, #DA70D6, #9370DB)",
            surface="rgba(30, 30, 30, 0.9)",
            text="#FFFFFF",
            text_secondary="#CCCCCC",
            border="rgba(255, 255, 255, 0.2)",
            success="#28C840",
            warning="#FFBD44",
            error="#FF5C5C",
            info="#4A9EFF"
        )
        
        self.themes["cosmic"] = Theme(
            name="Cosmic",
            type=ThemeType.COSMIC,
            colors=cosmic_colors,
            font_family="Segoe UI, Arial, sans-serif",
            font_size=12,
            border_radius=12,
            shadow="0 8px 32px rgba(0, 0, 0, 0.3)",
            animation_speed=300
        )
        
        # Dark Theme
        dark_colors = ColorScheme(
            primary="#BB86FC",
            secondary="#03DAC6",
            accent="#CF6679",
            background="linear-gradient(135deg, #1A1A1A, #2D2D2D, #404040)",
            surface="rgba(20, 20, 20, 0.95)",
            text="#FFFFFF",
            text_secondary="#B0B0B0",
            border="rgba(255, 255, 255, 0.1)",
            success="#4CAF50",
            warning="#FF9800",
            error="#F44336",
            info="#2196F3"
        )
        
        self.themes["dark"] = Theme(
            name="Dark",
            type=ThemeType.DARK,
            colors=dark_colors,
            font_family="Segoe UI, Arial, sans-serif",
            font_size=12,
            border_radius=8,
            shadow="0 4px 16px rgba(0, 0, 0, 0.5)",
            animation_speed=250
        )
        
        # Light Theme
        light_colors = ColorScheme(
            primary="#1976D2",
            secondary="#388E3C",
            accent="#F57C00",
            background="linear-gradient(135deg, #E3F2FD, #F3E5F5, #FFF3E0)",
            surface="rgba(255, 255, 255, 0.95)",
            text="#212121",
            text_secondary="#757575",
            border="rgba(0, 0, 0, 0.1)",
            success="#4CAF50",
            warning="#FF9800",
            error="#F44336",
            info="#2196F3"
        )
        
        self.themes["light"] = Theme(
            name="Light",
            type=ThemeType.LIGHT,
            colors=light_colors,
            font_family="Segoe UI, Arial, sans-serif",
            font_size=12,
            border_radius=8,
            shadow="0 2px 8px rgba(0, 0, 0, 0.1)",
            animation_speed=200
        )
        
        # Neon Theme
        neon_colors = ColorScheme(
            primary="#00FFFF",
            secondary="#FF00FF",
            accent="#FFFF00",
            background="linear-gradient(135deg, #0A0A0A, #1A0A1A, #0A1A0A)",
            surface="rgba(0, 0, 0, 0.9)",
            text="#00FFFF",
            text_secondary="#FF00FF",
            border="rgba(0, 255, 255, 0.5)",
            success="#00FF00",
            warning="#FFFF00",
            error="#FF0000",
            info="#00FFFF"
        )
        
        self.themes["neon"] = Theme(
            name="Neon",
            type=ThemeType.NEON,
            colors=neon_colors,
            font_family="Consolas, Monaco, monospace",
            font_size=11,
            border_radius=4,
            shadow="0 0 20px rgba(0, 255, 255, 0.5)",
            animation_speed=150
        )
        
        # Minimal Theme
        minimal_colors = ColorScheme(
            primary="#000000",
            secondary="#666666",
            accent="#000000",
            background="linear-gradient(135deg, #FFFFFF, #F5F5F5)",
            surface="rgba(255, 255, 255, 0.9)",
            text="#000000",
            text_secondary="#666666",
            border="rgba(0, 0, 0, 0.1)",
            success="#000000",
            warning="#666666",
            error="#000000",
            info="#000000"
        )
        
        self.themes["minimal"] = Theme(
            name="Minimal",
            type=ThemeType.MINIMAL,
            colors=minimal_colors,
            font_family="Helvetica, Arial, sans-serif",
            font_size=11,
            border_radius=2,
            shadow="none",
            animation_speed=100
        )
        
        # Ocean Theme
        ocean_colors = ColorScheme(
            primary="#00BCD4",
            secondary="#0097A7",
            accent="#4DD0E1",
            background="linear-gradient(135deg, #006064, #00838F, #00ACC1, #26C6DA)",
            surface="rgba(0, 0, 0, 0.8)",
            text="#FFFFFF",
            text_secondary="#B2EBF2",
            border="rgba(0, 188, 212, 0.3)",
            success="#4CAF50",
            warning="#FF9800",
            error="#F44336",
            info="#00BCD4"
        )
        
        self.themes["ocean"] = Theme(
            name="Ocean",
            type=ThemeType.OCEAN,
            colors=ocean_colors,
            font_family="Segoe UI, Arial, sans-serif",
            font_size=12,
            border_radius=10,
            shadow="0 6px 24px rgba(0, 188, 212, 0.3)",
            animation_speed=350
        )
    
    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme"""
        if theme_name in self.themes:
            self.current_theme = self.themes[theme_name]
            return True
        return False
    
    def get_theme(self, theme_name: str = None) -> Theme:
        """Get a theme by name or current theme"""
        if theme_name:
            return self.themes.get(theme_name)
        return self.current_theme
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names"""
        return list(self.themes.keys())
    
    def get_theme_stylesheet(self, theme_name: str = None) -> str:
        """Get CSS stylesheet for a theme"""
        theme = self.get_theme(theme_name) or self.current_theme
        if not theme:
            return ""
        
        colors = theme.colors
        
        return f"""
        /* {theme.name} Theme Stylesheet */
        QWidget {{
            font-family: {theme.font_family};
            font-size: {theme.font_size}px;
        }}
        
        QMainWindow {{
            background: {colors.background};
            color: {colors.text};
        }}
        
        QPushButton {{
            background: {colors.primary};
            color: white;
            border: none;
            border-radius: {theme.border_radius}px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background: {colors.secondary};
        }}
        
        QPushButton:pressed {{
            background: {colors.accent};
        }}
        
        QTextEdit {{
            background: {colors.surface};
            color: {colors.text};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            padding: 8px;
        }}
        
        QLabel {{
            color: {colors.text};
            background: transparent;
        }}
        
        QMenu {{
            background: {colors.surface};
            color: {colors.text};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            padding: 5px;
        }}
        
        QMenu::item {{
            padding: 8px 20px;
            border-radius: 4px;
        }}
        
        QMenu::item:selected {{
            background: {colors.primary};
        }}
        
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        
        QProgressBar {{
            background: {colors.surface};
            border: 1px solid {colors.border};
            border-radius: {theme.border_radius}px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background: {colors.primary};
            border-radius: {theme.border_radius}px;
        }}
        """
    
    def get_button_styles(self, button_type: str = "default") -> str:
        """Get specific button styles"""
        theme = self.current_theme
        if not theme:
            return ""
        
        colors = theme.colors
        
        if button_type == "close":
            return f"""
            QPushButton {{
                background: {colors.error};
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: #FF4444;
            }}
            QPushButton:pressed {{
                background: #CC3333;
            }}
            """
        elif button_type == "minimize":
            return f"""
            QPushButton {{
                background: {colors.warning};
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: #FFAA22;
            }}
            QPushButton:pressed {{
                background: #DD8800;
            }}
            """
        elif button_type == "maximize":
            return f"""
            QPushButton {{
                background: {colors.success};
                border-radius: 10px;
                border: none;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: #22AA33;
            }}
            QPushButton:pressed {{
                background: #1A8822;
            }}
            """
        
        return ""

# Global instance
theme_manager = ThemeManager()
