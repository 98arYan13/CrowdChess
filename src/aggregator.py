# this is aggregator for CrowdChess project
import functools
from collections import Counter
from flask import Blueprint, flash
from flask_login import current_user, login_required
from flask_socketio import emit, disconnect
from __init__ import socketio
from CHES import recommend_moves, get_fen, make_move, update_pgn_file


# aggregator blueprint
aggregator = Blueprint('aggregator', __name__)


active_users = set() # users present on users.html page
def act_users(method, active_users):
    if method == "add":
        active_users.add(current_user.email)
    elif method == "remove":
        active_users.remove(current_user.email)
    return active_users

# Using Flask-Login with Flask-SocketIO
def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

@socketio.on('connect', namespace='/users')
@login_required
def on_connect(auth):
    users_count = len(act_users('add', active_users))
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    emit('initialize_client_fen', {'fen' : fen})

@socketio.on('disconnect', namespace='/users')
@login_required
def test_disconnect():
    users_count = len(act_users('remove', active_users))
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    print(f'\nuser {current_user.name} leaved the main page\n')


# empty moves list
moves_list = []

# fen
fen = get_fen()

# Majority vote:
def aggregation(moves_list):
    """
    aggregate moves of users
    if moves do not reach the consesus, then show recommend choices to users
    for choose between them.
    NOTE: for variety of aggregations, function can be named to chosen aggregation method.
    THIS USE MAJORITY VOTE METHOD !
    """
    consensus = False
    if len(Counter(moves_list)) > 1: # if second most_common move exist (if different moves)
        if Counter(moves_list).most_common()[0][1] > Counter(moves_list).most_common()[1][1]: # if count of most frequent move is bigger than second most frequent (or actually all others)
            consensus_move = Counter(moves_list).most_common()[0][1] # if most frequent move is the Majority
            consensus = True # consensus reached
    elif len(Counter(moves_list)) == 1: # if all moves are the same
        consensus_move = moves_list[0]
        consensus = True # consensus reached
    if consensus:
        if len(consensus_move) > 4: # when recommend choice
            computer_move = consensus_move[4:]
            consensus_move = consensus_move[0:4]
        # update pgn file with given legall san
        update_pgn_file(consensus_move)
        global fen
        fen = get_fen() # FEN of current game
        print(fen)
        emit('user_move', fen, broadcast=True) # force client to move "consensus_move"
        # move for computer on client side
        if computer_move == None:
            computer_move = make_move()
            update_pgn_file(computer_move['best_move'])
        else:
            update_pgn_file(computer_move)
        fen = get_fen() # FEN of current game
        print(fen)
        emit('computer_move', computer_move, broadcast=True) # force client to move "computer_move"
    else:
        emit('consensus_not_reached', 'Consenus NOT reached! Please choose between recommended choices.', broadcast=True)
        emit('recommend_choice', recommend_moves(), broadcast=True)

@socketio.on("move_from_user", namespace='/users')
def move_from_user(move):
    print(f"\nmove form user {current_user.name}:", move, '\n')
    global moves_list
    moves_list.append(move['from'] + move['to'])
    print('moves_list=', moves_list, '    moves_list length: ', len(moves_list))
    print('active_users length: ', len(active_users))
    if len(moves_list) == len(active_users): # call aggregation if all users do thier move
        aggregation(moves_list)
        moves_list = [] # emptying moves list for next aggregation

@socketio.on("choice_from_user", namespace='/users')
def choice_from_user(choice):
    print(f"\nmove form user {current_user.name}:", choice, '\n')
    global moves_list
    moves_list.append(choice['uArrow'] + choice['oArrow']) # stringify uArrow and oArrow for simplicity of counter list
    print('moves_list=', moves_list, '    moves_list length: ', len(moves_list))
    if len(moves_list) == len(active_users): # call aggregation when all users do their move
        aggregation(moves_list)
        moves_list = [] # emptying moves list for next aggregation
