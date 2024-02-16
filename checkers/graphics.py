from asyncUi.window import Window, eventHandler
from asyncUi import events
from asyncUi.graphics import Box, VirticalGroup, HorizontalGroup, Circle, Clickable
from asyncUi.display import drawableRenderer, Drawable, Color, Point, Size, Scale, stackEnabler, AutomaticStack
from asyncUi.util import Placeholder, Inferable, MutableContextManager, CallbackWrapper, Callback
from . import engine
from contextlib import ExitStack
import pygame

pygame.init()



window = Window(pygame.display.set_mode((8*8*10, 8*8*10), pygame.RESIZABLE), "Checkers")
@eventHandler
def exiter(e: events.Quit) -> None:
    exit()
exiter.register()

class BoardBackground(Drawable, AutomaticStack):
    size = Placeholder[Size]((0, 0))
    def __init__(self, position: Inferable[Point], size: Size, grid_size: tuple[int, int], on_square_press: Callback[tuple[int, int]]) -> None:
        self.position = position
        self.size = size
        self.grid_size = grid_size
        self.on_square_press = CallbackWrapper(on_square_press)        

        self.box_size = (size[0] // grid_size[0], size[1] // grid_size[1])
        self.rows = VirticalGroup(position, [
            HorizontalGroup(..., [Box(..., self.box_size, [Color.WHITE, Color.BLACK][(i + row % 2) % 2]) for i in range(grid_size[0])])
        for row in range(grid_size[1])])

        self._clicker = Clickable(position, size, self._clickHandler)
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.rows.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'BoardBackground':
        return BoardBackground(position, self.size, self.grid_size, self.on_square_press)
    
    def cellPosition(self, cell: Point) -> Point:
        return self.box_size[0] * cell[0], self.box_size[1] * cell[1]
    
    def _clickHandler(self, e: events.MouseButtonUp) -> None:
        scale = Scale(window.scale_factor)
        real_pos = scale.point(e.pos)
        board_pos = real_pos[0] - self.position[0], real_pos[1] - self.position[1]

        self.on_square_press.invoke((board_pos[0] // self.box_size[0], board_pos[1] // self.box_size[1]))
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self._clicker)
    
class Pawn(Drawable):
    size = Placeholder[Size]((0, 0))
    def __init__(self, position: Inferable[Point], size: Size, color: Color) -> None:
        self.position = position
        self.size = size
        self.color = color

        self.shape = Circle(position, color, (size[0] + size[1]) // 4)
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.shape.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'Pawn':
        return Pawn(position, self.size, self.color)


class CheckersBoard(Drawable, AutomaticStack):
    size = Placeholder[Size]((0, 0))
    def __init__(self, position: Inferable[Point], size: Size, board: engine.Board) -> None:
        self.position = position
        self.size = size
        self.board = board

        board.on_board_change = self._onBoardChange
        
        self.background = BoardBackground(position, size, (board.board_width, board.board_height), self._onBackgroundClick)
        
        self.overlay: list[Drawable] = []
        self._selected_piece: Point | None = None

        #intialize everything
        board.on_board_change(board)
    
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)
        for piece in self.overlay:
            piece.draw(window, scale)

    def _onBackgroundClick(self, where: Point) -> None:
        if self._selected_piece is not None:
            self._make_move(where)
            self._selected_piece = None

        elif self.board[where] is None:
            self._selected_piece = None
        else:
            self._selected_piece = where
    def _make_move(self, where: Point) -> None:
        assert self._selected_piece is not None
        try:
            self.board.makeMove(engine.Move(self._selected_piece, where))
        except engine.InvalidMove as e :
            print(f"Failed to make move: {e}")
            
    def _onBoardChange(self, board: engine.Board) -> None:
        self.overlay = []
        for y in range(board.board_height):
            for x in range(board.board_width):
                match board[x, y]:
                    case engine.Pawn():
                        
                        self.overlay.append(
                            Pawn(
                                self.background.cellPosition((x,y)), 
                                self.background.box_size, 
                                self._player_color_mapping[board.current_player]
                            ))
    
    _player_color_mapping = {
        engine.Player.player1: Color.RED,
        engine.Player.player2: Color.BLACK
    }

    def reposition(self, position: Inferable[Point]) -> 'CheckersBoard':
        return CheckersBoard(position, self.size, self.board)

    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.background)
board = engine.Board(None, None, None)
board[1,1] = engine.Pawn(engine.Player.player1)
window.startRenderer(30, drawableRenderer(CheckersBoard((0, 0), window.orginal_size, board).__enter__()))
window.run()