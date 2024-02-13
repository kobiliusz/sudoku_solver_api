import sys
from solve import solve_sudoku, SudokuBoard, UnsolvableSudoku
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware

logger.remove()
logger.add("log/api_log", level='INFO', rotation="500 MB")

app = FastAPI()
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="sudoku_solver_frontend")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PuzzleData(BaseModel):
    puzzle: SudokuBoard


class SolutionData(BaseModel):
    solution: SudokuBoard


templates = Jinja2Templates(directory="frontend")


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )


@app.get("/favicon.ico", response_class=FileResponse)
async def read_item(request: Request):
    return templates.TemplateResponse(
        request=request, name="favicon.ico", context={}
    )


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
