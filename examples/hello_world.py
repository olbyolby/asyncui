# Import all nessisary modules, there is a lot, but that's just for shortening names.
from asyncui.window import Window, event_handler
from asyncui.graphics import Text, Group, Box
from asyncui.display import Color, drawable_renderer
from asyncui.resources.fonts import fonts
from asyncui import events
import pygame
import sys
# Initialize pygame, which is used by asyncui.
pygame.init()

# Create the window, it manages events and rendering. 
# The window has a size of (250, 100), but a UI size of (500, 200), and a title of "Hello world: asyncui".
# UI elements are automatically scaled to the window size from the UI size.
window = Window(pygame.display.set_mode((250, 100), pygame.RESIZABLE), (500, 200), "Hello world: asyncui")

# Load a font to render to window with, in this case, arial is used.
arial = fonts.load_system_font('arial')

# By default, the "X" button will do nothing, so an event handler is made to call exit() when "X" is pressed.
@event_handler
def exit_button(event: events.Quit) -> None:
    sys.exit()
# The event handler will not be called until it is registered, so it will now handle events.
exit_button.register()

# This creates the actual UI, it is put inside a group.
gui = Group(..., [
    # This creates the background, a white box with the size of the window.
    Box((0, 0), (500, 200), Color.WHITE), 
    # This creates the text, it is at (0, 0), with the arial font, font size of 32, and text color of black.
    Text((0, 0), arial, 32, Color.BLACK, "Hello world from asyncui!") 
])

# The GUI will not process IO unless it is enabled, which will start event handlers on the UI.
gui.enable()

# This wraps the widget in a rendering function and starts the process of rendering, at 15 FPS.
window.start_renderer(15, drawable_renderer(gui))

# This starts up the event loop and begins running. Kind of like asyncio's run.
window.run()