import sys
from solve import solve_sudoku, SudokuBoard, UnsolvableSudoku
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from loguru import logger


logger.remove()
logger.add(sys.stderr, level='INFO')

app = FastAPI()


class BoardData(BaseModel):
    puzzle: SudokuBoard


@app.post('/solve')
async def solve(board: BoardData, request: Request):
    logger.info('New request from {}', request.client.host)
    try:
        return solve_sudoku(board.puzzle)

    except UnsolvableSudoku:
        logger.warning('Request from {} contained unsolvable puzzle!', request.client.host)
        raise HTTPException(406, 'Provided puzzle is unsolvable')
