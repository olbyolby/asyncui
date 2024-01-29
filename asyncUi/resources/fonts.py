import pygame
import weakref
from typing import Callable
from enum import Enum

class FontSizeManager:
    def __init__(self, fontName: str, fontLoader: Callable[[str, int], pygame.font.Font]) -> None:
        self.fontLoader = fontLoader
        self.fontName = fontName
        self.loadedFonts = dict[int, pygame.font.Font]()
    def withSize(self, fontSize: int) -> pygame.font.Font:
        if fontSize in self.loadedFonts:
            return self.loadedFonts[fontSize]
        
        newFont = self.fontLoader(self.fontName, fontSize)
        self.loadedFonts[fontSize] = newFont
        return newFont
    def __getitem__(self, key: int) -> pygame.font.Font:
        return self.withSize(key)
    def __delitem__(self, key: int) -> None:
        del self.loadedFonts[key]


        
class FontManager:
    def __init__(self, defaultLoader: Callable[[str, int], pygame.font.Font] = pygame.font.SysFont) -> None:
        self.defaultLoader = defaultLoader
        self.loadedFonts = dict[str, FontSizeManager]()

    def loadLocalFont(self, fontName: str) -> FontSizeManager: 
        if fontName not in self.loadedFonts:
            self.loadedFonts[fontName] = FontSizeManager(fontName, pygame.font.Font)
        return self.loadedFonts[fontName]
        
    def loadSystemFont(self, fontName: str) -> FontSizeManager:
        if fontName not in self.loadedFonts:
            self.loadedFonts[fontName] = FontSizeManager(fontName, pygame.font.SysFont)
        return self.loadedFonts[fontName]
    
    def __getitem__(self, fontName: str) -> FontSizeManager:
        if fontName not in self.loadedFonts:
            self.loadedFonts[fontName] = FontSizeManager(fontName, self.defaultLoader)
        return self.loadedFonts[fontName]
    def __delitem__(self, fontName: str) -> None:
        del self.loadedFonts[fontName]
fontManager = FontManager(pygame.font.Font)

Font = FontSizeManager