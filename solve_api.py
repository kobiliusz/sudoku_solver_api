import sys
from solve import solve_sudoku, SudokuBoard, UnsolvableSudoku
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from loguru import logger


logger.remove()
logger.add(sys.stderr, level='INFO')

app = FastAPI()


class PuzzleData(BaseModel):
    puzzle: SudokuBoard


class SolutionData(BaseModel):
    solution: SudokuBoard


@app.post('/solve')
async def solve(board: PuzzleData, request: Request) -> SolutionData:
    logger.info('New request from {}', request.client.host)
    try:
        return SolutionData(solution=solve_sudoku(board.puzzle))

    except UnsolvableSudoku:
        logger.warning('Request from {} contained unsolvable puzzle!', request.client.host)
        raise HTTPException(406, 'Provided puzzle is unsolvable')
