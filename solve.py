from typing import List, Set
from annotated_types import Len, Ge, Le
from typing_extensions import Annotated
from abc import ABC, abstractmethod
from dataclasses import dataclass
from loguru import logger


SudokuIndex = Annotated[int, Ge(0), Le(8)]

SudokuValue = Annotated[int, Ge(0), Le(9)]

SudokuBoard = Annotated[
    List[
        Annotated[
            List[SudokuValue],
            Len(max_length=9, min_length=9)
        ]
    ],
    Len(max_length=9, min_length=9)
]

BoolSudokuBoard = Annotated[
    List[
        Annotated[
            List[bool],
            Len(max_length=9, min_length=9)
        ]
    ],
    Len(max_length=9, min_length=9)
]

ALL_VALUES = set(range(1, 10))


@dataclass
class SudokuCoords:
    row: SudokuIndex
    col: SudokuIndex


def copy_board(old: SudokuBoard):
    return [[old[r][c] for c in range(9)] for r in range(9)]


class SudokuGroup(ABC):
    board: SudokuBoard
    group_index: SudokuIndex

    def __init__(self, sud_board: SudokuBoard, group_idx: SudokuIndex):
        self.board = sud_board
        self.group_index = group_idx

    @abstractmethod
    def idx_to_coords(self, idx: SudokuIndex) -> SudokuCoords:
        pass

    @staticmethod
    @abstractmethod
    def init_by_coords(b: SudokuBoard, coords: SudokuCoords):
        pass

    def values(self) -> List[SudokuValue]:
        vals = []
        for i in range(9):
            coords = self.idx_to_coords(i)
            vals.append(self.board[coords.row][coords.col])
        return vals

    def empty_coords(self) -> List[SudokuCoords]:
        vals = []
        for i in range(9):
            coords = self.idx_to_coords(i)
            if self.board[coords.row][coords.col] == 0:
                vals.append(SudokuCoords(coords.row, coords.col))
        return vals

    def missing_vals(self) -> Set[SudokuValue]:
        return ALL_VALUES.difference(self.values())


class SudokuRow(SudokuGroup):
    def idx_to_coords(self, idx: SudokuIndex) -> SudokuCoords:
        return SudokuCoords(self.group_index, idx)

    @staticmethod
    def init_by_coords(b: SudokuBoard, coords: SudokuCoords):
        return SudokuRow(b, coords.row)


class SudokuCol(SudokuGroup):
    def idx_to_coords(self, idx: SudokuIndex) -> SudokuCoords:
        return SudokuCoords(idx, self.group_index)

    @staticmethod
    def init_by_coords(b: SudokuBoard, coords: SudokuCoords):
        return SudokuCol(b, coords.col)


# 0 1 2
# 3 4 5
# 6 7 8

class SudokuBlock(SudokuGroup):
    def idx_to_coords(self, idx: SudokuIndex) -> SudokuCoords:
        return SudokuCoords(self.group_index // 3 * 3 + idx // 3, self.group_index % 3 * 3 + idx % 3)

    @staticmethod
    def init_by_coords(b: SudokuBoard, coords: SudokuCoords):
        return SudokuBlock(b, coords.row // 3 * 3 + coords.col // 3)


def group_fill(group: SudokuGroup, coords: SudokuCoords) -> Set[SudokuGroup]:
    clses = {SudokuRow, SudokuCol, SudokuBlock}
    clses.remove(group.__class__)
    return {cls.init_by_coords(group.board, coords) for cls in clses}


@dataclass
class SudokuSnapshot:
    board: SudokuBoard
    moves: List[SudokuValue]
    coords: SudokuCoords

    def __post_init__(self):
        self.board = copy_board(self.board)


def init_groups(board: SudokuBoard) -> List[SudokuGroup]:
    ret = []
    for i in range(9):
        ret.append(SudokuRow(board, i))
        ret.append(SudokuCol(board, i))
        ret.append(SudokuBlock(board, i))
    return ret


def init_checked() -> BoolSudokuBoard:
    return [[False for c in range(9)] for r in range(9)]


def missing_vals_key(group: SudokuGroup) -> int:
    return len(group.missing_vals())


class SolvedIteration(Exception):
    pass


class UnsolvablePuzzle(Exception):
    pass


def solve_sudoku(init_board: SudokuBoard) -> SudokuBoard:
    snapshots: List[SudokuSnapshot] = []
    board: SudokuBoard = copy_board(init_board)
    logger.info("Starting solving board:\n{}", board)
    groups: List[SudokuGroup] = init_groups(board)
    checked: BoolSudokuBoard = None

    while True:
        try:
            logger.debug("Next iteration:\n{}", board)
            groups = sorted(groups, key=missing_vals_key)
            if len(groups[-1].missing_vals()) == 0:
                logger.info("Board solved:\n{}", board)
                return board
            min_fits = 10
            min_fits_coords: SudokuCoords = None
            min_fits_moves: List[SudokuValue] = None
            checked = init_checked()
            for group in groups:
                for empty_field in group.empty_coords():
                    if checked[empty_field.row][empty_field.col]:
                        continue
                    moves_set = group.missing_vals()
                    for fill_group in group_fill(group, empty_field):
                        moves_set = moves_set.intersection(fill_group.missing_vals())
                    moves = list(moves_set)

                    if len(moves) == 0:
                        if len(snapshots) == 0:
                            raise UnsolvablePuzzle
                        else:
                            logger.info("Restoring board from snapshot...")
                            snap = snapshots[-1]
                            next_move = snap.moves.pop()
                            if len(snap.moves) == 0:
                                snapshots.pop()
                            board = copy_board(snap.board)
                            groups = init_groups(board)
                            board[snap.coords.row][snap.coords.col] = next_move
                            raise SolvedIteration

                    elif len(moves) == 1:
                        board[empty_field.row][empty_field.col] = moves[0]
                        raise SolvedIteration

                    elif len(moves) < min_fits:
                        min_fits = len(moves)
                        min_fits_moves = [i for i in moves]
                        min_fits_coords = empty_field

                    checked[empty_field.row][empty_field.col] = True

            logger.info("No obvious solution, creating snapshot...")
            next_move = min_fits_moves.pop()
            snapshots.append(SudokuSnapshot(board, min_fits_moves, min_fits_coords))
            board[min_fits_coords.row][min_fits_coords.col] = next_move

        except SolvedIteration:
            continue

