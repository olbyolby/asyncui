import unittest
import asyncui.events as events
import pygame

class TestEvents(unittest.TestCase):
    #Fake key down
    pygame_key_down = pygame.event.Event(pygame.KEYDOWN,  {
        'key': pygame.K_LEFTPAREN,
        'mod': pygame.KMOD_SHIFT,
        'unicode': ')'
    })
    #Malformed mouse move
    pygame_mouse_move = pygame.event.Event(pygame.MOUSEMOTION, {
        'pos': (0, 0),
        'rel': (10, 4),
        'buttons': (1, 0, 0),
        #'touch': False # This is missing, making it malformed
    })
    def test_marshal(self) -> None:
        down = events.marshal(self.pygame_key_down)
        assert type(down) == events.KeyDown, f"Marshal returned an event of type {type(down)} when {events.KeyDown} was expected"
        assert down.type == self.pygame_key_down.type, "Type is not preserved py marshal"
        assert down.unicode == self.pygame_key_down.unicode, "attribute is not preserved by marshal"
        assert down.key == events.keyboard.Keys.LeftParen, "attribute is not preserved by marshal"
        
        try:
            events.marshal(self.pygame_mouse_move)
        except ValueError:
            pass # This is intended, it should raise a value error
        else:
            raise AssertionError("A malformed event constructed without an error('touch' was missing for MouseButtonDown event, but value error was never raised)")
    def test_to_pygame_event(self) -> None:
        down = events.marshal(self.pygame_key_down)
        # Key_down should be built in to asyncui, so this should never fail
        assert down is not None

        # If a pygame event is used with marshal, then the inverse should return an equavialent event
        assert events.to_pygame_event(down) == self.pygame_key_down, "to_pygame_event fails to return a proper pygame event, even when contructed with one"

        # This forces asyncui to generate a new pygame event
        down._orgin_event = None
        # to_pygame_event sometimes adds exctra keys because to event internal data,
        # but it should always contain at least the same keys and values as the orginal event.
        print(events.to_pygame_event(down), self.pygame_key_down)
        assert vars(events.to_pygame_event(down)).items() >= vars(self.pygame_key_down).items(), "to_pygame_event does not properly generate pygame event from asyncui event"
if __name__ == "__main__":
    unittest.main()