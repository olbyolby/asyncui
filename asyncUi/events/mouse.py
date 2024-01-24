import pygame
from typing import NewType

Button = NewType('Button', int)
class Buttons:
    left = Button(pygame.BUTTON_LEFT)
    middle = Button(pygame.BUTTON_MIDDLE)
    right = Button(pygame.BUTTON_RIGHT)
