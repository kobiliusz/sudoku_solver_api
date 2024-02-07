import sys
from solve import solve_sudoku, SudokuBoard, UnsolvableSudoku
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware


logger.remove()
logger.add("log/api_log", level='INFO', rotation="500 MB")

app = FastAPI()

allowed_origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PuzzleData(BaseModel):
    puzzle: SudokuBoard


class SolutionData(BaseModel):
    solution: SudokuBoard


# noinspection PyBroadException
@app.post('/solve')
async def solve(board: PuzzleData, request: Request) -> SolutionData:
    logger.info('New request from {}:{}', request.client.host, request.client.port)
    try:
        return SolutionData(solution=solve_sudoku(board.puzzle))

    except UnsolvableSudoku:
        logger.warning('Request from {} contained unsolvable puzzle!', request.client.host)
        raise HTTPException(406, 'Provided puzzle is unsolvable')

    except Exception:
        logger.exception('API Exception!')
