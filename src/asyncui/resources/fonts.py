"""
Files for more convenient working with fonts

Classes:
    FontSizeManager - Provides an interface for getting a font of different sizes
    FontManager - Manages different types of fonts and provides a convenient interface to access them
Globals:
    fonts - An instance of FontManager, which manages all loaded fonts for you
"""
import pygame
from typing import Callable

class FontSizeManager:
    """
    Font size manager, provides interface for changing a font size

    Methods:
        with_size(pt) - returns the font with a size given by pt
    Operators:
        __getitem__(pt) [pt] - returns the font with the given font size
        __delitem__(pt) del [pt] - removes the font from the loaded font list 
    """
    def __init__(self, font_name: str, font_loader: Callable[[str, int], pygame.font.Font]) -> None:
        self.font_loader = font_loader
        self.font_name = font_name
        self.loaded_fonts = dict[int, pygame.font.Font]()
    def with_size(self, fontSize: int) -> pygame.font.Font:
        if fontSize in self.loaded_fonts:
            return self.loaded_fonts[fontSize]
        
        new_font = self.font_loader(self.font_name, fontSize)
        self.loaded_fonts[fontSize] = new_font
        return new_font
    def __getitem__(self, key: int) -> pygame.font.Font:
        return self.with_size(key)
    def __delitem__(self, key: int) -> None:
        del self.loaded_fonts[key]

class FontManager:
    """
    A manager for magaging different fonts by name

    Methods:
        load_local_font(name) - loads a given font with name using pygame.font.Font and returns it
        load_system_font(name) - loads the given font with name using pygame.font.SysFont and returns it
        cache_font(font) - adds a font to the font cache, which will be used if the font is loaded again
    Operators: 
        __getitem__ [name] - loads the font with the given name and returns it using the default font loader
        __delitem__ del [name] - deletes the font from the cache
    """
    def __init__(self, default_loader: Callable[[str, int], pygame.font.Font] = pygame.font.SysFont) -> None:
        self.default_loader = default_loader
        self.loaded_fonts = dict[str, FontSizeManager]()

    def cache_font(self, font: FontSizeManager) -> FontSizeManager:
        self.loaded_fonts[font.font_name] = font
        return font
    def load_local_font(self, font_name: str) -> FontSizeManager: 
        if font_name in self.loaded_fonts:
            return self.loaded_fonts[font_name]
        return FontSizeManager(font_name, pygame.font.Font)
        
    def load_system_font(self, font_name: str) -> FontSizeManager:
        if font_name not in self.loaded_fonts:
            return self.loaded_fonts[font_name]
        return FontSizeManager(font_name, pygame.font.SysFont)
    
    def __getitem__(self, font_name: str) -> FontSizeManager:
        if font_name not in self.loaded_fonts:
            self.loaded_fonts[font_name] = FontSizeManager(font_name, self.default_loader)
        return self.loaded_fonts[font_name]
    def __delitem__(self, font_name: str) -> None:
        del self.loaded_fonts[font_name]

Font = FontSizeManager