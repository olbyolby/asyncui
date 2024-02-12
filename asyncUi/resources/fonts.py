import pygame
from typing import Callable

class FontSizeManager:
    def __init__(self, font_name: str, font_loader: Callable[[str, int], pygame.font.Font]) -> None:
        self.font_loader = font_loader
        self.font_name = font_name
        self.loaded_fonts = dict[int, pygame.font.Font]()
    def withSize(self, fontSize: int) -> pygame.font.Font:
        if fontSize in self.loaded_fonts:
            return self.loaded_fonts[fontSize]
        
        newFont = self.font_loader(self.font_name, fontSize)
        self.loaded_fonts[fontSize] = newFont
        return newFont
    def __getitem__(self, key: int) -> pygame.font.Font:
        return self.withSize(key)
    def __delitem__(self, key: int) -> None:
        del self.loaded_fonts[key]


        
class FontManager:
    def __init__(self, default_loader: Callable[[str, int], pygame.font.Font] = pygame.font.SysFont) -> None:
        self.default_loader = default_loader
        self.loaded_fonts = dict[str, FontSizeManager]()

    def loadLocalFont(self, font_name: str) -> FontSizeManager: 
        if font_name not in self.loaded_fonts:
            self.loaded_fonts[font_name] = FontSizeManager(font_name, pygame.font.Font)
        return self.loaded_fonts[font_name]
        
    def loadSystemFont(self, fontName: str) -> FontSizeManager:
        if fontName not in self.loaded_fonts:
            self.loaded_fonts[fontName] = FontSizeManager(fontName, pygame.font.SysFont)
        return self.loaded_fonts[fontName]
    
    def __getitem__(self, fontName: str) -> FontSizeManager:
        if fontName not in self.loaded_fonts:
            self.loaded_fonts[fontName] = FontSizeManager(fontName, self.default_loader)
        return self.loaded_fonts[fontName]
    def __delitem__(self, fontName: str) -> None:
        del self.loaded_fonts[fontName]
fontManager = FontManager(pygame.font.Font)

Font = FontSizeManager