# chess processes for CrowdChess (CHES)
from flask import request
from flask.blueprints import Blueprint
import chess
import chess.engine
import chess.pgn
import io
import time
import random
import config


CHES = Blueprint('CHES', __name__)

# FEN for start game
FEN = config.FEN

# create a new PGN file
pgn_file_name = config.pgn_file_name
with open('./data/' + pgn_file_name, 'w', encoding="utf-8") as pgn:
    game = chess.pgn.Game()
    if FEN:
        game.setup(FEN)
    exporter = chess.pgn.FileExporter(pgn)
    game.end().accept(exporter)

# update pgn file with given legall san
def update_pgn_file(SAN):
    with open('./data/' + pgn_file_name, 'r') as pgn:
        game = chess.pgn.read_game(pgn)
    with open('./data/' + pgn_file_name, 'w') as pgn:
        game.end().add_variation(game.end().board().push_san(SAN))
        exporter = chess.pgn.FileExporter(pgn)
        game.accept(exporter)

# FEN of current game
def get_fen():
    with open('./data/' + pgn_file_name, 'r') as pgn:
        game = chess.pgn.read_game(pgn)
    board = game.board()
    return board.fen()


# Maximum legal moves for current playable color
@CHES.route('/max_legal_moves', methods=['POST'])
def max_legal_moves():
    try:
        # TODO: better to use fen instead of pgn
        pgn = request.form.get('pgn')
        game = chess.pgn.read_game(io.StringIO(pgn))
        board = game.board()
        for move in game.mainline_moves():
            board.push(move)
        return {'max_legal_moves': board.legal_moves.count()}
    except: # if new game
        return {'max_legal_moves': '20'}

# make move from aggregator
def make_move():
    # open pgn file
    with open('./data/' + pgn_file_name, 'r') as pgn:
        # read game from PGN
        game = chess.pgn.read_game(pgn)

    # board based on last game
    board = game.end().board()

    # create chess engine instance
    engine = chess.engine.SimpleEngine.popen_uci(
        './engine/stockfish_13/stockfish_13_win_x64_bmi2.exe')
    
    # extract fixed depth value
    fixed_depth = request.form.get('fixed_depth')

    # extract move time value
    move_time = request.form.get('move_time')

    # move_time by default if none
    if move_time == None:
        move_time = config.move_time

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
    """
    # if fixed depth is available
    if fixed_depth != '0':
        try:
            # search for best move instantly
            info = engine.analyse(board, chess.engine.Limit(depth=int(fixed_depth)))
        except:
            info = {}
    """
    
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
@CHES.route('/recommend_moves', methods=['POST'])
def recommend_moves():
    # number of multipv lines for recommended moves
    MULTIPV = config.MULTIPV

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
    
    # move_time by default if none
    if move_time == None:
        move_time = config.move_time

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

    """
    # if fixed depth is available
    if fixed_depth != '0':
        try:
            # search for best move instantly
            info = engine.analyse(
                board, chess.engine.Limit(depth=int(fixed_depth)), multipv=MULTIPV)
        except:
            info = {}
    """
    
    # terminate engine process
    engine.quit()
    
    # randomising info dict for create a serie of random ordered recommend moves
    random.shuffle(info)

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


