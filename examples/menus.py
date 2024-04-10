# Import all nessisary modules, there is a lot, but that's just for shortening names.
from asyncui.window import Window, event_handler
from asyncui.graphics import Text, Group, Box, OptionBar, Button, OptionMenu
from asyncui.display import Color, drawable_renderer
from asyncui.resources.fonts import FontManager
from asyncui import events
import pygame
import sys
# Initialize pygame, which is used by asyncui.
pygame.init()

# Create the window, it manages events and rendering. 
# The window has a size of (250, 100), but a UI size of (500, 200), and a title of "Hello world: asyncui".
# UI elements are automatically scaled to the window size from the UI size.
window = Window(pygame.display.set_mode((250, 100), pygame.RESIZABLE), (500, 200), "Hello world: asyncui")

# Create a font loader, it handles the loading of fonts
fonts = FontManager()

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
    Box((0, 0), (500, 200), Color.WHITE),
    OptionBar((0, 0), (500, 25), [
        Button(..., Text(..., arial, 32, Color.BLACK, "Exit"), sys.exit),
        OptionMenu(..., (50, 100), Button(..., Text(..., arial, 32, Color.BLACK, "Options"), ...), [
            Button(..., Text(..., arial, 32, Color.BLACK, "Option A"), lambda: print("Option A")),
            Button(..., Text(..., arial, 32, Color.BLACK, "Option B"), lambda: print("Option B")),
            Button(..., Text(..., arial, 32, Color.BLACK, "Option C"), lambda: print("Option C")),
        ])
    ])
])

# The GUI will not process IO unless it is enabled, which will start event handlers on the UI.
gui.enable()

# This wraps the widget in a rendering function and starts the process of rendering, at 15 FPS.
with gui:
    window.start_renderer(15, drawable_renderer(gui))

    # This starts up the event loop and begins running. Kind of like asyncio's run.
    window.run()