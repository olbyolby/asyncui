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
@dataclass
class Move:
    start: Point
    target: Point

@dataclass(eq=False)
class Peice:
    owner: Player
    @abstractmethod
    def validMoves(self, board: CheckerBoard, position: Point) -> list[Point]:
        pass
    @abstractmethod
    def reachedEdge(self, board: CheckerBoard, position: Point) -> Peice:
        pass
    @abstractmethod
    def findCaptures(self, board: CheckerBoard, position: Point, new_position: Point) -> tuple[list[Peice]]:
        pass

class Pawn(Peice):
    def reachedEdge(self, board: CheckerBoard, position: Point) -> Peice:
        return self
    @listify
    def validMoves(self, board: CheckerBoard, position: Point) -> Iterable[Point]:
        x, y = position
        if board[x-1,y-1] is None:
            yield x-1, y-1
        if board[x+1,y-1] is None:
            yield x+1, y-1
        if board[x+1,y+1] is None:
            yield x+1, y+1
        if board[x-1,y+1] is None:
            yield x-1, y+1

class Player(Enum):
    player1 = True
    player2 = False
    
class CheckerBoard:
    def __init__(self) -> None:

        # Initialze the board
        self.board_data: list[list[Peice | None]] = [[None]*8]*8

        self.player_turn = Player.player1

    def makeMove(self, move: Move) -> None:
        piece = self.board_data[move.start[0]][move.start[1]]
        if piece is None:
            raise ValueError("No such peice")

        if piece.owner != self.player_turn:
                    raise ValueError("Invalid turn")
        
        valid_moves = piece.validMoves(self, move.start)
        if move.target not in valid_moves:
            raise ValueError("Invalid move, inassesible position")
        
        
        
        captures, = piece.findCaptures(self, move.start, move.target)
        for captured in captures:
            for column in self.board_data:
                if captured in column:
                    column.remove(piece)
                    break
    
        self.board_data[move.start[0]][move.start[1]] = None
        self.board_data[move.target[0]][move.target[1]] = piece
        self.player_turn = self.nextTurn()

    def nextTurn(self) -> Player:
        turns = [Player.player1, Player.player2]
        return turns[(turns.index(self.player_turn) + 1) % len(turns)]  
    
    def __getitem__(self, pos: Point) -> Peice | None:
        return self.board_data[pos[0]][pos[1]] 
    def __setitem__(self, pos: Point, value: Peice | None) -> None:
        if value is not None:
            if (value.owner == Player.player1 and pos[1] == 0) or (value.owner == Player.player2 and pos[1] == 7):
                value = value.reachedEdge(self, pos)
        self.board_data[pos[0]][pos[1]] = value
        
    