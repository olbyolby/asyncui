from __future__ import annotations
from enum import Enum, auto
from abc import abstractmethod
from dataclasses import dataclass
from typing import TypeVar, TypeVarTuple, Iterable, Callable

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

@dataclass
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
        i += 1
        yield (start[0] + offset[0] * i, start[1] + offset[1] * i)
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
    def reachedEdge(self, board: Board, position: Point) -> Piece:
        return self
    @listify
    def validMoves(self, board: Board, position: Point) -> Iterable[Point]:
        flip = 1 if self.owner == Player.player2 else -1
        # Check corners
        move_left = take(2, diagnal(position, (flip, flip)))
        if board.onBoard(move_left[0]) and board[move_left[0]] is None:
            yield move_left[0]
        elif board.onBoard(move_left[1]) and (target:=board[move_left[0]]) is not None and target.owner != self.owner:
            yield move_left[1]


        move_right = take(2, diagnal(position, (-flip, flip)))
        if board.onBoard(move_right[0]) and board[move_right[0]] is None:
            yield move_right[0]
        elif board.onBoard(move_right[1]) and (target:=board[move_right[0]]) is not None and target.owner != self.owner:
            yield move_right[1]
    def __str__(self) -> str:
        return 'pw'
    
    def captures(self, board: Board, move: Move) -> list[Piece]:
        flip = -1 if self.owner == Player.player2 else 1
        # Check corners
        move_left = take(2, diagnal(move.target, (flip, flip)))
        move_right = take(2, diagnal(move.target, (-flip, flip)))

        if move_left[1] == move.start:
            return [assertNotNone(board[move_left[0]])]
        if move_right[1] == move.start:
            return [assertNotNone(board[move_right[0]])]
        return []

@dataclass
class Move:
    start: Point
    target: Point

class InvalidMove(Exception):
    def __init__(self, move: Move, message: str) -> None:
        self.move = move
        super().__init__(message)
class Board:
    board_width = 8
    board_height = 8
    def __init__(self, board_change: Callable[[Board], None] | None = None, score_change: Callable[[Board], None] | None = None, player_change: Callable[[Board], None] | None = None) -> None:
        self.on_board_change = board_change
        self.on_score_change = score_change
        self.on_player_change = player_change
        
        self.board_state: list[Piece | None] = list[Piece | None]([None]) * self.board_width* self.board_height
        for y in range(self.board_height):
            for x in range(self.board_width):
                if x % 2 == 0:
                    owner = engine

        
        self.current_player = Player.player1
        
    def __getitem__(self, index: Point) -> Piece | None:
        x, y = index
        return self.board_state[y * self.board_width + x]
    def __setitem__(self, index: Point, value: Piece | None) -> None:
        x, y = index
        self.board_state[y * self.board_width + x] = value

        if value is not None:
            if value.owner == Player.player1 and y == self.board_height-1:
                self.board_state[y * self.board_width + x] = value.reachedEdge(self, index)
            elif value.owner == Player.player2 and y == 0:
                self.board_state[y * self.board_width + x] = value.reachedEdge(self, index)

        if self.on_board_change is not None: 
            self.on_board_change(self)
    def onBoard(self, point: Point) -> bool:
        return 0 <= point[0]  <= self.board_width and 0 <= point[1] <= self.board_height

    def nextMove(self) -> None:
        players = [Player.player1, Player.player2]
        self.current_player = players[(players.index(self.current_player)+1) % len(players)]
        if self.on_player_change is not None: 
            self.on_player_change(self)

    def makeMove(self, move: Move) -> None:
        piece = self[move.start]
        if piece is None:
            raise InvalidMove(move, f"No piece at {move.start}")
        
        if piece.owner != self.current_player:
            raise InvalidMove(move, f"Invalid ownership of piece at {move.start}")
        if move.target not in piece.validMoves(self, move.start):
            raise InvalidMove(move, f"Invalid move {move.start}")
        
        
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

