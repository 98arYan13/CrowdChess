# packages
from flask import Flask, Response, redirect, url_for, \
    request, session, abort, render_template, jsonify
from flask_login import LoginManager, UserMixin, \
    login_required, login_user, logout_user, current_user
import chess
import chess.engine
import chess.pgn
import io
import random
from datetime import datetime
import json
import config

# create web app instance
app = Flask(__name__)


# root(index) route
@app.route('/')
def root():
    return render_template('index.html')

# Maximum legal moves for current playable color
@app.route('/max_legal_moves', methods=['POST'])
def max_legal_moves():
    try:
        pgn = request.form.get('pgn')
        game = chess.pgn.read_game(io.StringIO(pgn))
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        return {'max_legal_moves': board.legal_moves.count()}
    except: # if new game
        return {'max_legal_moves': '20'}

# make move API
@app.route('/make_move', methods=['POST'])
def make_move():
    # extract PGN string from HTTP POST request body
    pgn = request.form.get('pgn')
    
    try:
        # read game moves from PGN
        game = chess.pgn.read_game(io.StringIO(pgn))

        # init board
        board = game.board()

        # loop over moves in game
        for move in game.mainline_moves():
            # make move on chess board
            board.push(move)
    
    except:
        # extract fen string from HTTP POST request body
        fen = request.form.get('fen')
        board = chess.Board(fen)
        
    # create chess engine instance
    engine = chess.engine.SimpleEngine.popen_uci(
        './engine/stockfish_13/stockfish_13_win_x64_bmi2.exe')
    
    # extract fixed depth value
    fixed_depth = request.form.get('fixed_depth')

    # extract move time value
    move_time = request.form.get('move_time')
    
    # if move time is available
    if move_time != '0':
        if move_time == 'instant':
            try:
                # search for best move instantly
                info = engine.analyse(board, chess.engine.Limit(time=0.1))
            except:
                info = {}
        else:
            try:
                # search for best move with fixed move time
                info = engine.analyse(board, chess.engine.Limit(time=int(move_time)))
            except:
                info = {}

    # if fixed depth is available
    if fixed_depth != '0':
        try:
            # search for best move instantly
            info = engine.analyse(board, chess.engine.Limit(depth=int(fixed_depth)))
        except:
            info = {}
    
    # terminate engine process
    engine.quit()
    
    try:
        # extract best move from PV
        best_move = info['pv'][0]

        # update internal python chess board state
        board.push(best_move)
        
        # get best score
        try:
            score = -int(str(info['score'])) / 100
        
        except:
            score = str(info['score'])
            
            # inverse score
            if '+' in score:
                score = score.replace('+', '-')
            
            elif '-' in score:
                score = score.replace('-', '+')
        
        return {
            'fen': board.fen(),
            'best_move': str(best_move),
            'score': score,
            'depth': info['depth'],
            'pv': ' '.join([str(move) for move in info['pv']]),
            'nodes': info['nodes'],
            'time': info['time'],
        }
    
    except:
        return {
            'fen': board.fen(),
            'score': '#+1',
        }

# Recommended moves
@app.route('/recommend_moves', methods=['POST'])
def recommend_moves():
    # set number of multipv lines for recommended moves
    MULTIPV = 3

    # extract PGN string from HTTP POST request body
    pgn = request.form.get('pgn')
    
    try:
        # read game moves from PGN
        game = chess.pgn.read_game(io.StringIO(pgn))

        # init board
        board = game.board()

        # loop over moves in game
        for move in game.mainline_moves():
            # make move on chess board
            board.push(move)
    
    except:
        # extract fen string from HTTP POST request body
        fen = request.form.get('fen')
        board = chess.Board(fen)
        
    # create chess engine instance
    engine = chess.engine.SimpleEngine.popen_uci(
        './engine/stockfish_13/stockfish_13_win_x64_bmi2.exe')
    
    # extract fixed depth value
    fixed_depth = request.form.get('fixed_depth')

    # extract move time value
    move_time = request.form.get('move_time')
    
    # if move time is available
    if move_time != '0':
        if move_time == 'instant':
            try:
                # search for best move instantly
                info = engine.analyse(
                    board, chess.engine.Limit(time=0.1), multipv=MULTIPV)
            except:
                info = {}
        else:
            try:
                # search for best move with fixed move time
                info = engine.analyse(
                    board, chess.engine.Limit(time=int(move_time)), multipv=MULTIPV)
            except:
                info = {}

    # if fixed depth is available
    if fixed_depth != '0':
        try:
            # search for best move instantly
            info = engine.analyse(
                board, chess.engine.Limit(depth=int(fixed_depth)), multipv=MULTIPV)
        except:
            info = {}
    
    # terminate engine process
    engine.quit()
    
    print('best move is: ', info[0]['pv'][0])

    print("\ninfo:\n", info)
    random.shuffle(info)

    print("randomised first pv: ", info[0]['pv'][0])
    print("\ninfo_shuffled:\n", info)
        
    return {
        'fen': board.fen(),
        'score_array': [str(i['score']) for i in info],
        'depth_array': [str(i['depth']) for i in info],
        'pv_array': [' '.join([str(move) for move in i['pv']]) for i in info]
    }

"""
@app.route('/analytics')
def analytics():
    return render_template('stats.html')

@app.route('/analytics/api/post', methods=['POST'])
def post():
    response = Response('')
    response.headers['Access-Control-Allow-Origin'] = '*'

    stats = {
        'Date': request.form.get('date'),
        'Url': request.form.get('url'),
        'Agent':request.headers.get('User-Agent')
    }

    if request.headers.getlist("X-Forwarded-For"):
       stats['Ip'] = request.headers.getlist("X-Forwarded-For")[0]
    else:
       stats['Ip'] = request.remote_addr
    
    if request.headers.get('Origin'):
        stats['Origin'] = request.headers.get('Origin')
    else:
        stats['Origin'] = 'N/A'
    
    if request.headers.get('Referer'):
        stats['Referer'] = request.headers.get('Referer')
    else:
        stats['Referer'] = 'N/A'
    
    with open('stats.json', 'a') as f: f.write(json.dumps(stats, indent=2) + '\n\n')
    return response


@app.route('/analytics/api/get')
def get():
    stats = []
    
    with open('stats.json') as f:
        for entry in f.read().split('\n\n'):
            try: stats.append(json.loads(entry))
            except: pass
              
    return jsonify({'data': stats})
"""

# main driver
if __name__ == '__main__':
    # start HTTP server
    app.run(debug=True, threaded=True)
