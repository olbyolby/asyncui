from asyncUi.window import Window, eventHandler
from asyncUi import events
from asyncUi.graphics import Box, Circle, Clickable, Text, Polygon, Line 
from asyncUi.display import drawableRenderer, Drawable, Color, Point, Size, Scale, stackEnabler, AutomaticStack
from asyncUi.util import Placeholder, Inferable, CallbackWrapper, Callback
from asyncUi.resources.fonts import fontManager
from . import engine
from contextlib import ExitStack
import pygame

pygame.init()



window = Window(pygame.display.set_mode((8*8*10, 8*8*10*(9/8)), pygame.RESIZABLE), "Checkers")

@eventHandler
def exiter(e: events.Quit) -> None:
    exit()
exiter.register()
arial = fontManager.loadSystemFont('arial')

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
                    case engine.Pawn() as piece:
                        offset = self.background.cellPosition((x,y))
                        self.overlay.append(
                            Pawn(
                                (offset[0] + self.position[0], offset[1] + self.position[1]), 
                                self.background.box_size, 
                                self._player_color_mapping[piece.owner]
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


class TeamInfoLeft(Drawable):
    size = Placeholder((0, 0))
    def __init__(self, position: Inferable[Point], size: Size, status_color: Color) -> None:
        self.position = position
        self.size = size
        self.status_color = status_color

        name = Text(..., arial, round(size[0]*(4/45)), Color.BLACK, "Red")
        name = name.reposition((self.position[0] + size[0] - name.size[0], self.position[1]))
        self.name = name
   

        overshoot = round(size[0]*(4/45))
        self.outline = Polygon((name.position[0] - overshoot, self.position[1]), Color.BLACK, [
            (0,0),
            (overshoot, name.size[1]),
            (overshoot + name.size[0], name.size[1]),
            (overshoot + name.size[0], 0),
        ], round(size[0]*(2/159)))

        status_length = round(size[0]*(4/79))
        self.status = Box((self.position[0] + size[0] - status_length, self.position[1] + name.size[1]), (status_length, size[1] - name.size[1]), status_color)
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.status.draw(window, scale)
        self.name.draw(window, scale)
        self.outline.draw(window, scale)
        
    def reposition(self, position: Inferable[Point]) -> 'TeamInfoLeft':
        return TeamInfoLeft(position, self.size, self.status_color)
    
class BoardInfo(Drawable):
    size = Placeholder((0, 0))
    def __init__(self, position: Inferable[Point], size: Size, current_team: engine.Player) -> None:
        self.position = position
        self.size = size
        self.current_team = current_team

        x, y = self.position
        line_thickness = size[1] // 20
        self.background = Box(position, size, Color(255, 255//2, 0))
        self.background_seperator = Line((x, y - line_thickness), Color.BLACK, line_thickness, (0, 0), (size[0], 0))
        self.team_seperator = Line((self.position[0] + size[0] // 2 - line_thickness//2, self.position[1]), Color.BLACK, line_thickness, (0, 0), (0, size[1]))
        
        self.left_info = TeamInfoLeft(position, (size[0] // 2 - line_thickness, size[1]), Color.GREEN if current_team is engine.Player.player1 else Color.RED)


    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.background.draw(window, scale)
        self.background_seperator.draw(window, scale)
        self.team_seperator.draw(window, scale)

        self.left_info.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'BoardInfo':
        return BoardInfo(position, self.size, self.current_team)
    
    def changePlayer(self, current_team: engine.Player) -> 'BoardInfo':
        return BoardInfo(self.position, self.size, current_team)    

board = engine.Board(None, None, None)
class Game(Drawable, AutomaticStack):
    size = Placeholder[Size]((0,0))
    def __init__(self, position: Inferable[Point], size: Size) -> None:
        self.position = position
        self.size = size

        board = engine.Board(None, None, self._updateCurrentTeam)
        self.board_info = BoardInfo(position, (size[0], size[1]//9), board.current_player)
        self.board = CheckersBoard((self.position[0], self.position[1] + size[1]//9), (size[0], size[1] - size[1] // 9), board)
    def draw(self, window: pygame.Surface, scale: float) -> None:
        self.board_info.draw(window, scale)
        self.board.draw(window, scale)
    def reposition(self, position: Inferable[Point]) -> 'Game':
        raise NotImplementedError()
    
    def _updateCurrentTeam(self, board: engine.Board) -> None:
        self.board_info = self.board_info.changePlayer(board.current_player)
    @stackEnabler
    def enable(self, stack: ExitStack) -> None:
        stack.enter_context(self.board)


#window.startRenderer(30, drawableRenderer(CheckersBoard((0, 0), window.orginal_size, board).__enter__()))
window.startRenderer(30, drawableRenderer(Game((0, 0), window.orginal_size).__enter__()))
window.run()