# this is aggregator for CrowdChess project
import functools
from collections import Counter
from flask import Blueprint
from flask_login import current_user, login_required
from flask_socketio import emit, disconnect
from __init__ import socketio
from CHES import (recommend_moves, get_fen, make_move, update_pgn_file,
    take_back, fen_history)


# aggregator blueprint
aggregator = Blueprint('aggregator', __name__)


moves_list = [] # empty moves list
fen, max_legal_moves = get_fen() # fen and Maximum legal moves for current playable color
prevent_drag = False # prevent client board to drag move
recommend_moves_obj = None # availiblity of recommend choices
last_move_san = None # san of last approved move by server
active_users = set() # users present on users.html page
users_count = 0 # number of active users on main page
glowing_time = '0ms' # glowing time
take_back_votes_count = 0 # number of votes to take_back move


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
    global users_count, active_users
    active_users.add(current_user.email)
    users_count = len(active_users)
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    emit('update_client_interface', {
        'fen':fen,
        'max_legal_moves':max_legal_moves,
        'glowing_time':glowing_time,
        'take_back_votes_count':take_back_votes_count})
    emit('preventDrag', prevent_drag)
    emit('recommendMovesObj', recommend_moves_obj)

@socketio.on('disconnect', namespace='/users')
@login_required
def test_disconnect():
    global users_count, active_users
    active_users.remove(current_user.email)
    users_count = len(active_users)
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    print(f'\nuser {current_user.name} leaved the main page\n')


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
    computer_move = 'xxxx'
    global prevent_drag
    if len(Counter(moves_list)) > 1: # if second most_common move exist (if different moves)
        if Counter(moves_list).most_common()[0][1] > Counter(moves_list).most_common()[1][1]: # if count of most frequent move is bigger than second most frequent (or actually all others)
            consensus_move = Counter(moves_list).most_common()[0][0] # if most frequent move is the Majority
            consensus = True # consensus reached
    elif len(Counter(moves_list)) == 1: # if all moves are the same
        consensus_move = moves_list[0]
        consensus = True # consensus reached

    if consensus:
        global recommend_moves_obj
        recommend_moves_obj = None
        print('\nconsensus reached\n')
        if len(consensus_move) > 4: # when recommend choice
            computer_move = consensus_move[4:]
            consensus_move = consensus_move[0:4]
        # update pgn file with given legall san
        update_pgn_file(consensus_move)
        global fen, max_legal_moves, last_move_san
        last_move_san = consensus_move
        fen, max_legal_moves = get_fen() # FEN of current game
        last_move_from, last_move_to = last_move_san[0:2], last_move_san[2:]
        emit('update_client_interface', {
            'fen':fen,
            'max_legal_moves':max_legal_moves,
            'last_move_from':last_move_from,
            'last_move_to':last_move_to
            }, broadcast=True) # force client to move "consensus_move"
        last_move_san = computer_move
        # move for computer on client side
        if computer_move == 'xxxx':
            computer_move = make_move()
            last_move_san = computer_move['best_move']
            update_pgn_file(computer_move['best_move'])
        else:
            update_pgn_file(computer_move)
        fen, max_legal_moves = get_fen() # FEN of current game
        last_move_from, last_move_to = last_move_san[0:2], last_move_san[2:]
        emit('update_client_interface', {
            'fen':fen,
            'max_legal_moves':max_legal_moves,
            'last_move_from':last_move_from,
            'last_move_to':last_move_to
            }, broadcast=True) # force client to move "computer_move"
        prevent_drag = False
        emit('preventDrag', prevent_drag, broadcast=True)

    else:
        print('consensus not reached, recommendation')
        if last_move_san: # for first move, there is no last_move_san
            last_move_from, last_move_to = last_move_san[0:2], last_move_san[2:]
            emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves, 'last_move_from':last_move_from,
            'last_move_to':last_move_to}, broadcast=True) # force client to move "computer_move"
        else:
            emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves}, broadcast=True) # force client to move "computer_move"
        emit('consensus_not_reached', 'Consenus NOT reached! Please choose between recommended choices.', broadcast=True)
        recommend_moves_obj = recommend_moves()
        emit('recommend_choice', recommend_moves_obj, broadcast=True)


@socketio.on("move_from_user", namespace='/users')
def move_from_user(move):
    emit('preventDrag', True)
    print(f"\nmove form user {current_user.name}:", move, '\n')
    global moves_list
    moves_list.append(move['from'] + move['to'])
    print('moves_list=', moves_list, '    moves_list length: ', len(moves_list))
    print('active_users length: ', len(active_users))
    if len(moves_list) >= len(active_users): # call aggregation if all active users do thier move
        global prevent_drag
        prevent_drag = True
        emit('preventDrag', prevent_drag, broadcast=True)
        aggregation(moves_list)
        moves_list = [] # emptying moves list for next aggregation

@socketio.on("choice_from_user", namespace='/users')
def choice_from_user(choice):
    print(f"\nmove form user {current_user.name}:", choice, '\n')
    global moves_list
    moves_list.append(choice['uArrow'] + choice['oArrow']) # stringify uArrow and oArrow for simplicity of counter list
    print('moves_list=', moves_list, '    moves_list length: ', len(moves_list))
    if len(moves_list) >= len(active_users): # call aggregation when all active users do their move
        aggregation(moves_list)
        moves_list = [] # emptying moves list for next aggregation


take_back_votes = set() # users voted to take_back
@socketio.on("vote_take_back", namespace='/users')
def vote_take_back():
    """
    This is for collect votes from users that want to take_back chess
    to their previous move.
    If users push take_back button then send a signal to back that she
    votes take_back. But if she pushe the button again,
    this means cansel that vote.
    If 2/3 of all active users voted to take_bake, so it applies.
    ( 2/3 is optional )
    """
    if len(fen_history) >= 3: # for take_back it must at least 3 fen exist (1 remain with 2 move pop)
        if current_user.email not in take_back_votes: # if user pushed take_back button
            take_back_votes.add(current_user.email)
        else:                                         # if user pushed take_back button again
            take_back_votes.remove(current_user.email)

        print('\ntake_back_votes :', take_back_votes)
        global glowing_time, take_back_votes_count, fen, max_legal_moves
        take_back_votes_count = len(take_back_votes)
        if (take_back_votes_count == 0) or (users_count == 0):
            glowing_time = '0ms'
        elif take_back_votes_count / users_count >= (2/3) : # if more than 2/3 of users vote to take_back
            take_back() # consensus to do take_back
            fen, max_legal_moves = get_fen() # FEN of current game
            emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves}, broadcast=True) # force client to take_back
            glowing_time = '0ms'
            take_back_votes.clear()
            take_back_votes_count = 0
        else:
            glowing_time = str(int(3000 - (3000-20) / ((2/3) * users_count - 1)
                * (take_back_votes_count - 1))) + 'ms'

        emit('glow_take_back_button', {'glowing_time':glowing_time,
            'take_back_votes_count':take_back_votes_count}, broadcast=True)
