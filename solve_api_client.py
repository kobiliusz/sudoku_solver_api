from icecream import ic
from requests import get, post
import json


def use_api(req_board):
    url = 'http://127.0.0.1:8000/solve/'
    request_data = json.dumps({'puzzle': req_board})
    return post(url, data=request_data).json()


if __name__ == '__main__':
    dosuku_resp = get('https://sudoku-api.vercel.app/api/dosuku')
    board = dosuku_resp.json()['newboard']['grids'][0]['value']

    ic(board)

    resp = use_api(board)

    ic(resp)

