import pygame
from typing import NamedTuple
from enum import Enum

class Button(Enum):
    left = pygame.BUTTON_LEFT
    right = pygame.BUTTON_RIGHT
    middle = pygame.BUTTON_MIDDLE
class Buttons:
    def __init__(self, buttons: tuple[int, int, int]):
        self.buttons = buttons
        self.left = bool(buttons[pygame.BUTTON_LEFT])
        self.right = bool(buttons[pygame.BUTTON_RIGHT])
        self.middle = bool(buttons[pygame.BUTTON_MIDDLE])
    def isDown(self, button: Button) -> bool:
        return bool(self.buttons[button.value])
    def __eq__(self, other: object | int | Button) -> bool:
        if not isinstance(other, Button | int):
            return NotImplemented

        if isinstance(other, Button):
            other = other.value
        return bool(self.buttons[other])
