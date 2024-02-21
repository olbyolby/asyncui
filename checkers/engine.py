from __future__ import annotations
from enum import Enum, auto
from abc import abstractmethod
from dataclasses import dataclass
from typing import TypeVar, TypeVarTuple, Iterable, Callable
from itertools import pairwise
from functools import wraps

T = TypeVar('T')
Ts = TypeVarTuple('Ts')
def listify(function: Callable[[*Ts], Iterable[T]]) -> Callable[[*Ts], list[T]]:
    def wrapper(*args: *Ts) -> list[T]:
        return list(function(*args))
    return wrapper

Point = tuple[int, int]

class Player(Enum):
    player1 = auto()
    player2 = auto()

@dataclass(eq=False)
class Piece:
    owner: Player
    @abstractmethod
    def reachedEdge(self, board: Board, position: Point) -> Piece:
        pass
    @abstractmethod
    def validMoves(self, board: Board, position: Point) -> list[Point]:
        pass
    @abstractmethod
    def captures(self, board: Board, move: Move) -> list[Piece]:
        pass
    @abstractmethod
    def __str__(self) -> str:
        pass


def addPoints(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]
def diagnal(start: Point, offset: Point) -> Iterable[Point]:
    i = 0
    while True:
        yield (start[0] + offset[0] * i, start[1] + offset[1] * i)
        i += 1
@listify
def take(ammount: int, values: Iterable[T]) -> Iterable[T]:
    for i, value in enumerate(values):
        if i >= ammount:
            break
        yield value
def assertNotNone(value: T | None, msg: str | None = None) -> T:
    assert value is not None, msg or "Invalid None"
    return value

class Pawn(Piece):
    def reachedEdge(self, board: Board, position: Point) -> King:
        return King(self.owner)
    @listify
    def validMoves(self, board: Board, position: Point) -> Iterable[Point]:
        flip = 1 if self.owner == Player.player2 else -1
        # Check corners
        move_left = take(3, diagnal(position, (flip, flip)))
        if board.onBoard(move_left[1]) and board[move_left[1]] is None:
            yield move_left[1]
        elif board.onBoard(move_left[2]) and board[move_left[2]] is None and (target:=board[move_left[1]]) is not None and target.owner != self.owner:
            yield move_left[2]


        move_right = take(3, diagnal(position, (-flip, flip)))
        if board.onBoard(move_right[1]) and board[move_right[1]] is None:
            yield move_right[1]
        elif board.onBoard(move_right[2]) and board[move_right[2]] is None and (target:=board[move_right[1]]) is not None and target.owner != self.owner:
            yield move_right[2]
    def __str__(self) -> str:
        return 'pw'
    
    def captures(self, board: Board, move: Move) -> list[Piece]:
        flip = -1 if self.owner == Player.player2 else 1
        # Check corners
        move_left = take(3, diagnal(move.target, (flip, flip)))
        move_right = take(3, diagnal(move.target, (-flip, flip)))

        if move_left[2] == move.start:
            return [assertNotNone(board[move_left[1]])]
        if move_right[2] == move.start:
            return [assertNotNone(board[move_right[1]])]
        return []

class King(Piece):
    def reachedEdge(self, board: Board, position: Point) -> Piece:
        return self

    @listify
    def validMoves(self, board: Board, position: Point) -> Iterable[Point]:
        for direction in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            for i, (point, next_point) in enumerate(pairwise(diagnal(position, direction))):
                if not board.onBoard(point):
                    break

                if (target:=board[point]) is None:
                    yield point
                elif board.onBoard(next_point) and board[next_point] is None and target.owner != self.owner:
                    yield next_point
                    break
                elif i != 0:
                    break


    def captures(self, board: Board, move: Move) -> list[Piece]:
        for direction in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            for i, (previous, point) in enumerate(pairwise(diagnal(move.start, direction))):
                if point == move.target:
                    if board.onBoard(previous) and (target:=board[previous]) is not None and target.owner != self.owner:
                        return [target]
                    else:
                        return []
                if not board.onBoard(point):
                    break
        raise AssertionError("Unreacahble")
    def __str__(self) -> str:
        return "KK"

@dataclass
class Move:
    start: Point
    target: Point

class InvalidMove(Exception):
    def __init__(self, move: Move, message: str, user_message: str | None = None) -> None:
        self.move = move
        self.user_message = user_message or message
        super().__init__(message)
class Board:
    board_width = 8
    board_height = 8
    def __init__(self, board_change: Callable[[Board], None] | None = None, win: Callable[[Board, Player], None] | None = None, player_change: Callable[[Board], None] | None = None) -> None:
        self.on_board_change = board_change
        self.on_win = win
        self.on_player_change = player_change
        self.ended = False
        
        self.board_state: list[Piece | None] = list[Piece | None]([None]) * self.board_width* self.board_height
        offset = 0
        for y in range(self.board_height):
            offset =  y  % 2
            for x in range(self.board_width):
                if x % 2 == offset:
                    if y < self.board_height*(3/8):
                        self[x, y] = Pawn(Player.player2)
                    elif y > self.board_height*(3/8) + self.board_height*(2/8) - 1:
                        self[x, y] = Pawn(Player.player1)
        
        self.current_player = Player.player1

    @staticmethod
    def requiredRunning(func: Callable[[Board, *Ts], T]) -> Callable[[Board, *Ts], T]:
        @wraps(func)
        def wrapper(self: Board, *args: *Ts) -> T:
            if self.ended is True:
                raise RuntimeError(f"Checkers game must be running to call f{func.__name__}")
            return func(self, *args)
        return wrapper
    
    def __getitem__(self, index: Point) -> Piece | None:
        x, y = index
        return self.board_state[y * self.board_width + x]
    def __setitem__(self, index: Point, value: Piece | None) -> None:
        x, y = index
        self.board_state[y * self.board_width + x] = value

        if value is not None:
            if value.owner == Player.player2 and y == self.board_height-1:
                self.board_state[y * self.board_width + x] = value.reachedEdge(self, index)
            elif value.owner == Player.player1 and y == 0:
                self.board_state[y * self.board_width + x] = value.reachedEdge(self, index)

        if self.on_board_change is not None: 
            self.on_board_change(self)
    
    def onBoard(self, point: Point) -> bool:
        return 0 <= point[0]  < self.board_width and 0 <= point[1] < self.board_height

    @requiredRunning
    def nextMove(self) -> None:
        players = [Player.player1, Player.player2]
        next_player = players[players.index(self.current_player) - 1]
        
        if self.checkLose(next_player) is True:
            self.ended = True
            if self.on_win is not None:
                self.on_win(self, self.current_player)

        self.current_player = next_player
        if self.on_player_change is not None: 
            self.on_player_change(self)

        
        
    def checkLose(self, player: Player) -> bool:
        for x in range(self.board_width):
            for y in range(self.board_height):
                if (target:=self[x,y]) is not None and target.owner != player and target.validMoves(self, (x,y)) != []:
                    return False
        return True

    @requiredRunning
    def makeMove(self, move: Move) -> None:
        piece = self[move.start]
        if piece is None:
            raise InvalidMove(move, f"No piece at {move.start}", f"There is no piece at {move.start}")
        
        if piece.owner != self.current_player:
            raise InvalidMove(move, f"Invalid ownership of piece at {move.start}", f"You do not own the piece at {move.start}")
        if move.target not in piece.validMoves(self, move.start):
            raise InvalidMove(move, f"Invalid move {move.start}", "That is an illegal move")
        
        
        captured = piece.captures(self, move)
        for captured_piece in captured:
            self.board_state[self.board_state.index(captured_piece)] = None

        if self[move.target] is not None:
            raise ValueError("Cannont overwrite non-empty peice!")
        self[move.target] = piece
        self[move.start] = None

        self.nextMove()

        
    def printBoard(self) -> None:
        print(' ' + '--'*self.board_width)
        for y in range(self.board_height):
            print('|', end='')
            for x in range(self.board_width):
                piece = self[x,y]
                if piece is None:
                    print('  ', end='')
                else:
                    print(str(piece), end='')
            print('|')
        print(' ' + '--'*self.board_width)

