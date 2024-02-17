import sys
from solve import solve_sudoku, SudokuBoard, UnsolvableSudoku
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from loguru import logger
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse
import os
import time


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Check if the request is HTTPS or running locally
        if request.url.scheme != "https" and request.headers.get("X-Forwarded-Proto") != "https":
            url = request.url.replace(scheme="https", port=443)
            return RedirectResponse(url=url, status_code=307)
        return await call_next(request)


logger.remove()
logger.add(sys.stderr, level='INFO')

app = FastAPI()
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="sudoku_solver_frontend")

origins = [
    "*"
]

if os.environ.get('SUDOKU_SOLVER_MODE', 'dev') == 'prod':
    app.add_middleware(HTTPSRedirectMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
async def return_index(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={}
    )


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('frontend/favicon.ico')


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
