import solve
from icecream import ic
from requests import get

if __name__ == '__main__':
    resp = get('https://sudoku-api.vercel.app/api/dosuku')
    b = resp.json()['newboard']['grids'][0]['value']

    ic(b)

    b = solve.solve_sudoku(b)

    ic(b)
