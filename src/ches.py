# chess processes for CrowdChess (ches)


from flask import Blueprint
from flask_socketio import emit
import chess
import chess.engine
import chess.pgn
import pandas as pd
from pandas import read_csv
import time
import random
import config


ches = Blueprint('ches', __name__)


FEN = config.FEN # FEN for start game
starttime  = time.strftime('%Y-%m-%d %H:%M:%S') # start of game
endtime = None # end of game
game_result = None # last game outcome
_depth = config.DEPTH # last chess engine depth
users_color = "White" # default color of the Crowd (users)


def read_games_stats():
    """games stats"""

    global _depth

    try:
        df_game = read_csv('./datas/all_games_stats.csv')
    except:
        # initialize all games stats
        df_game = pd.DataFrame(columns=[
            'startime',
            'endtime',
            'engine_depth',
            'result',
            'users_color'
            'users_count',
        ])

        df_game = df_game.append(pd.DataFrame([{
            'engine_depth': _depth,
        }]))

        # create xlsx file
        df_game.to_csv('./datas/all_games_stats.csv', index=False)
        df_game = read_csv('./datas/all_games_stats.csv')

    _depth = df_game['engine_depth'].iloc[-1]

    return df_game


def update_game_stats():
    """update games stats"""

    from aggregator import users_count

    df_game = read_games_stats()
    endtime  = time.strftime('%Y-%m-%d %H:%M:%S')

    # current game stats
    dict_game = {
        'startime': starttime,
        'endtime': endtime,
        'engine_depth': _depth,
        'result': game_result,
        'users_color': users_color,
        'users_count': users_count,
    }

    df_game = df_game.append(pd.DataFrame([dict_game]))
    df_game.to_csv('./datas/all_games_stats.csv', index=False)



# disable take_back button at begining of game
disable_take_back = True

# create a new PGN file
pgn_file_name = None
def create_new_pgn():
    global pgn_file_name, users_color
    pgn_file_name = config.pgn_file_name
    with open('./datas/' + pgn_file_name, 'w', encoding="utf-8") as pgn:
        game = chess.pgn.Game()
        game.headers['Date'] = time.strftime("%Y.%m.%d")
        game.headers['White'] = "Crowd"
        game.headers['Black'] = "Computer"
        users_color = "White"

        if FEN:
            game.setup(FEN)
            if not chess.Board(FEN).turn:
                game.headers['White'] = "Computer"
                game.headers['Black'] = "Crowd"
                users_color = "Black"

        exporter = chess.pgn.FileExporter(pgn)
        game.end().accept(exporter)

# update pgn file with given legall san
def update_pgn_file(SAN):
    with open('./datas/' + pgn_file_name, 'r') as pgn:
        game = chess.pgn.read_game(pgn)
    with open('./datas/' + pgn_file_name, 'w') as pgn:
        game.end().add_variation(chess.Move.from_uci(SAN))
        exporter = chess.pgn.FileExporter(pgn)
        game.accept(exporter)

    global game_result
    game_result = None

    board = game.board()
    for move in game.mainline_moves():
        board.push(move)

    # if game has an outcome
    outcome = board.outcome()
    if outcome:
        game_result = outcome.result()
        print(outcome.termination)
        if outcome.winner == chess.WHITE:
            if users_color == 'White':
                emit('game_is_over',
                    'Congratulations, We WON!\nGet Ready for the Next Round.')
            else:
                emit('game_is_over',
                    'We LOST!\nGet Ready for the Next Round.')

        elif outcome.winner == chess.BLACK:
            if users_color == 'Black':
                emit('game_is_over',
                    'Congratulations, We WON!\nGet Ready for the Next Round.')
            else:
                emit('game_is_over',
                    'We LOST!\nGet Ready for the Next Round.')

        time.sleep(20)
        new_game()

        from aggregator import update_client_interface
        update_client_interface()


# FEN of current game
def get_fen():
    with open('./datas/' + pgn_file_name, 'r') as pgn:
        game = chess.pgn.read_game(pgn)
    board = game.end().board()
    fen = board.fen()
    max_legal_moves = board.legal_moves.count()
    print('\nnew fen:', fen, '\n')
    fen_hist(fen)
    return fen, max_legal_moves

# storing fen history of every played moves
fen_history = []
def fen_hist(fen):
    global fen_history
    fen_history.append(fen)
    if len(fen_history) == 2 and fen_history[0] == fen_history[1]: # prevent duplicate first fen
        fen_history.pop()
    print(fen_history)


# make move from aggregator
def make_move():
    # open pgn file
    with open('./datas/' + pgn_file_name, 'r') as pgn:
        # read game from PGN
        game = chess.pgn.read_game(pgn)

    # board based on last game
    board = game.end().board()

    # create chess engine instance
    engine = chess.engine.SimpleEngine.popen_uci(
        './engine/stockfish_13/stockfish_13_win_x64_bmi2.exe')
    
    info = engine.analyse(board, chess.engine.Limit(depth=int(_depth)))

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
def recommend_moves():
    # number of multipv lines for recommended moves
    MULTIPV = config.MULTIPV

    # open pgn file
    with open('./datas/' + pgn_file_name, 'r') as pgn:
        # read game from PGN
        game = chess.pgn.read_game(pgn)

    # board based on last game
    board = game.end().board()
        
    # create chess engine instance
    engine = chess.engine.SimpleEngine.popen_uci(
        './engine/stockfish_13/stockfish_13_win_x64_bmi2.exe')

    # search for best move instantly
    info = engine.analyse(
        board, chess.engine.Limit(depth=int(_depth)),
        multipv=MULTIPV
        )

    print('\n',info,'\n')
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


def take_back():
    """
    take_back move to previous game of users.
    (for simplicity, game continues based on new pgn.
    because every time that take_back called, pgn gets a little difficult to handle.
    but this is not a good idea! it is better to create a new node on
    previous move in the main pgn file)
    """
    global fen_history, FEN
    fen_history.pop()
    fen_history.pop()
    FEN = fen_history[-1] # set FEN to last element of fen_history list
    create_new_pgn() # create a new pgn file with updated name


def new_game():
    """new game"""

    global fen_history, FEN, game_result, starttime
    fen_history.clear()
    FEN = None

    update_game_stats()

    create_new_pgn() # create a new pgn file with updated name

    starttime  = time.strftime('%Y-%m-%d %H:%M:%S')


create_new_pgn() # create a new pgn file with updated filename
