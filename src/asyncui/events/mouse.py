"""
Enumeration for mouse buttons

Enums:
    Button - You'll never guess
"""
import pygame
from enum import Enum

class Button(Enum):
    left = pygame.BUTTON_LEFT
    right = pygame.BUTTON_RIGHT
    middle = pygame.BUTTON_MIDDLE
    x1 = pygame.BUTTON_X1
    x2 = pygame.BUTTON_X2
    scrollWheelDown = pygame.BUTTON_WHEELDOWN
    scroolWheelUp = pygame.BUTTON_WHEELUP

