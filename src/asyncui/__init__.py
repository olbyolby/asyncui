"""
Asyncui is a widget based graphics library, built to work with pygame and with asyncio.

Modules:
    events - a collection of events handled by asyncui, provides wrappers for pygame events
    display - contains classes and functions for creating new asyncui widgets
    graphics - a collection of pre built graphics widgets for use in your own UIs
    window - provides the window class and indigration with asyncio
    utils - contains many utility functions used by asyncui
    resources - management of loaded resources, like fonts or images
"""

from . import *  # noqa: F403