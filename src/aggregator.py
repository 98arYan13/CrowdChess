# this is aggregator for CrowdChess project
from collections import Counter
from flask import Blueprint, flash
from flask_login import current_user
from flask_socketio import emit
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

@socketio.on('connect', namespace='/users')
def on_connect(auth):
    users_count = len(act_users('add', active_users))
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)

@socketio.on('disconnect', namespace='/users')
def test_disconnect():
    users_count = len(act_users('remove', active_users))
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    print('\nuser leaved the main page\n')


# empty moves list
moves_list = []
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
        # update pgn file with given legall san
        update_pgn_file(consensus_move)
        fen = get_fen() # FEN of current game
        emit('user_move', fen) # force client to move "consensus_move"
        # move for computer on client side
        computer_move = make_move()
        emit('computer_move', computer_move) # force client to move "computer_move"
    else:
        flash('Consenus NOT reached, please choose between recommended choices')
        emit('recommend_choice', recommend_moves())
    moves_list = [] # emptying moves list for next aggregation

@socketio.on("move_from_user", namespace='/users')
def move_from_user(move):
    print("\nmove form user: ", move, '\n')
    moves_list.append(move['san'])
    if len(moves_list) == len(active_users): # call aggregation if all users do thier move
        aggregation(moves_list)