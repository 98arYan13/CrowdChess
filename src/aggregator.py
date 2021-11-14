# this is aggregator for CrowdChess project


import functools
import time
from collections import Counter
from flask import Blueprint
from flask_login import current_user, login_required
from flask_socketio import emit, disconnect
from __init__ import socketio, language
from ches import (recommend_moves, get_fen, make_move, update_pgn_file,
    take_back, new_game, fen_history)


# aggregator blueprint
aggregator = Blueprint('aggregator', __name__)


moves_list = [] # empty moves list
moves_dict = {} # dictionary of users(keys) and their moves(values)
votes = [] # list of yes or no votes
fen, max_legal_moves = get_fen() # fen and Maximum legal moves for current playable color
prevent_drag = False # announce prevent client board to drag move
agg_announce = False # aggregation announcement
modal_announce = False # modal dialog announcement
recommend_moves_obj = None # availiblity of recommend choices
last_move_san = None # san of last approved move by server
active_users = set() # users present on main page
users_count = 0 # number of users present on main page
take_back_votes_count = 0 # number of votes to take_back move
take_back_percentage = '' # percentage of users that want take_back
new_game_votes_count = 0 # number of votes to new_game
new_game_percentage = '' # percentage of users that want new_game
countdown_aggregation_on = False # true if countdown_aggregation() is running
countdown_modal_on = False # true if countdown_modal() is running

def update_client_interface():
    global fen, max_legal_moves, take_back_percentage, prevent_drag,\
        recommend_moves_obj, new_game_percentage

    emit('update_client_interface', {
        'fen': fen,
        'max_legal_moves': max_legal_moves,
        'take_back_percentage': take_back_percentage,
        'new_game_percentage': new_game_percentage,
        'prevent_drag': prevent_drag,
        'recommend_moves_obj': recommend_moves_obj
    }, broadcast=True)


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
    active_users.add(current_user.email_phone)
    users_count = len(active_users)
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    emit('update_client_interface', {
        'fen':fen,
        'max_legal_moves':max_legal_moves,
        'take_back_percentage':take_back_percentage,
        'take_back_votes_count':take_back_votes_count})
    emit('preventDrag', prevent_drag)
    emit('recommendMovesObj', recommend_moves_obj)

@socketio.on('disconnect', namespace='/users')
@login_required
def test_disconnect():
    global users_count, active_users
    active_users.remove(current_user.email_phone)
    users_count = len(active_users)
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)
    print(f'\nuser {current_user.name} leaved the main page\n')


def countdown_aggregation(t):
    """countdown timer for waiting to aggregate
    """
    global countdown_aggregation_on
    countdown_aggregation_on = True
    print('\nTimer ON')
    emit('countdown_chess', 60, broadcast=True) # countdown timer for chess for 60s
    for _ in range(t):
        if agg_announce == False:
            time.sleep(1)
        else:
            print('\nTimer aborted')
            emit('stop_countdown_chess', broadcast=True)
            countdown_aggregation_on = False
            return

    countdown_aggregation_on = False
    print('\nTimer OFF')
    emit('stop_countdown_chess', broadcast=True)

    # call aggregaion if timeout
    emit('remove_recommend_choice', broadcast=True) # remove recommend_choice if any client has it
    aggregation(moves_list)
    moves_list.clear() # emptying moves list for next aggregation
    moves_dict.clear()

# Plurality vote:
def aggregation(moves_list):
    """
    aggregate moves of users
    if moves do not reach the consesus, then show recommend choices to users
    for choose between them.
    NOTE: for variety of aggregations, function can be named to chosen aggregation method.
    THIS USE PLURALITY VOTE METHOD !
    """
    consensus = False
    computer_move = 'xxxx'
    global prevent_drag, agg_announce
    prevent_drag = True 
    agg_announce = True # prevent countdown to call aggregation
    emit('preventDrag', prevent_drag, broadcast=True)

    if len(Counter(moves_list)) > 1: # if second most_common move exist (if different moves)
        if Counter(moves_list).most_common()[0][1] > Counter(moves_list).most_common()[1][1]: # if count of most frequent move is bigger than second most frequent (or actually all others)
            consensus_move = Counter(moves_list).most_common()[0][0] # if most frequent move is the Majority
            consensus = True # consensus reached
    elif len(Counter(moves_list)) == 1: # if all moves are the same
        consensus_move = moves_list[0]
        consensus = True # consensus reached

    if consensus:
        global recommend_moves_obj, take_back_votes, new_game_votes
        take_back_votes.clear() # when consensus reached, all secondary votes must be ignored
        new_game_votes.clear() # when consensus reached, all secondary votes must be ignored
        recommend_moves_obj = None
        print('\nconsensus reached\n')

        if len(consensus_move) > 8: # when recommend choice
            computer_move = consensus_move[5:]

        if consensus_move[4] == 'x':
            consensus_move = consensus_move[0:4]
        else:
            consensus_move = consensus_move[0:5]

        # update pgn file with given legall san
        update_pgn_file(consensus_move)
        global fen, max_legal_moves, last_move_san
        last_move_san = consensus_move[0:4]
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
        emit(
            'consensus_not_reached',
            language["consensus_not_reached"],
            broadcast=True
        )
        recommend_moves_obj = recommend_moves()
        emit('recommend_choice', recommend_moves_obj, broadcast=True)

    time.sleep(1)
    agg_announce = False


@socketio.on("move_from_user", namespace='/users')
@login_required
def move_from_user(move):
    emit('preventDrag', True)
    print(f"\nmove form user {current_user.name}:", move, '\n')
    global moves_list, moves_dict

    try:
        if moves_dict[current_user.email_phone]: # check double moving
            pass

    except:
        try: # check if there is pawn promotion to queen (to queen promotion is default)
            moves_list.append(move['from'] + move['to'] + move['promotion'])
        except:
            moves_list.append(move['from'] + move['to'] + 'x')

    moves_dict[current_user.email_phone] = move['from'] + move['to']
    print('moves_list=', moves_list, '    moves_list length: ', len(moves_list))
    print('active_users length: ', len(active_users))

    if len(moves_list) >= len(active_users): # call aggregation if all active users do their move
        aggregation(moves_list)
        moves_list.clear() # emptying moves list for next aggregation
        moves_dict.clear()

    elif len(moves_list) >= len(active_users) * 0.5 and not countdown_aggregation_on: # if half of active users do their move
        countdown_aggregation(60) # wait for other users' move for 60 second, then call aggregation


@socketio.on("choice_from_user", namespace='/users')
@login_required
def choice_from_user(choice):
    print(f"\nmove form user {current_user.name}:", choice, '\n')
    global moves_list, moves_dict

    try:
        if moves_dict[current_user.email_phone]: # check double moving
            pass

    except: # stringify uArrow and oArrow for simplicity of counter list
        if len(choice['uArrow']) == 4:
            moves_list.append(choice['uArrow'] + 'x' + choice['oArrow'])
        else: # if there is pawn promotion to queen
            moves_list.append(choice['uArrow'] + choice['oArrow'])

    moves_dict[current_user.email_phone] = choice['uArrow'] + choice['oArrow']
    print('moves_list=', moves_list, '    moves_list length: ', len(moves_list))
    if len(moves_list) >= len(active_users): # call aggregation when all active users do their move
        emit('remove_recommend_choice', broadcast=True) # remove recommend_choice if any client has it
        aggregation(moves_list)
        moves_list.clear() # emptying moves list for next aggregation
        moves_dict.clear()

    elif len(moves_list) >= len(active_users) * 0.5 and not countdown_aggregation_on: # if half of active users do their move
        countdown_aggregation(60) # wait for other users' move for 60 second, then call aggregation


new_game_votes = set() # users voted to take_back
@socketio.on("vote_new_game", namespace='/users')
@login_required
def vote_new_game():
    """
    This is for collect votes from users that want to new_game.
    If users push new_game button then send a signal to back that she
    votes new_game. But if she push the button again,
    this means cancel that vote.
    If 1/2 of all active users voted to new_game, a dialog apear to all users
    to choose Yes or No. If half of them again choose Yes, so it applies.
    ( 1/2 is optional )
    """
    global new_game_percentage ,max_legal_moves, fen,\
        new_game_votes_count, new_game_votes
    if len(fen_history) >= 3: # for new_game it must at least 3 fen exist (1 remain with 2 move pop)
        if current_user.email_phone not in new_game_votes: # if user pushed new_game button
            new_game_votes.add(current_user.email_phone)
        else:                                         # if user pushed new_game button again
            new_game_votes.remove(current_user.email_phone)

        print('\nnew_game_votes :', new_game_votes)
        new_game_votes_count = len(new_game_votes)
        if (new_game_votes_count == 0) or (users_count == 0):
            new_game_percentage = ''
        elif new_game_votes_count / users_count >= (1/2) : # if more than 1/2 of users vote to new_game
            msg = language["are_you_agree_new_game"]
            show_modal('new_game', msg) # show a modal dialog on users page to ask them choose Yes or No for new_game method

        else:
            new_game_percentage = str(int(new_game_votes_count / users_count
                * 100)) + '%'

        emit('new_game_percentage', {'new_game_percentage':
            new_game_percentage}, broadcast=True)


take_back_votes = set() # users voted to take_back
@socketio.on("vote_take_back", namespace='/users')
@login_required
def vote_take_back():
    """
    This is for collect votes from users that want to take_back chess
    to their previous move.
    If users push take_back button then send a signal to back that she
    votes take_back. But if she push the button again,
    this means cancel that vote.
    If 1/2 of all active users voted to take_bake, a dialog apear to all users
    to choose Yes or No. If half of them again choose Yes, so it applies.
    ( 1/2 is optional )
    """
    global take_back_percentage ,max_legal_moves, fen,\
        take_back_votes_count, take_back_votes
    if len(fen_history) >= 3: # for take_back it must at least 3 fen exist (1 remain with 2 move pop)
        if current_user.email_phone not in take_back_votes: # if user pushed take_back button
            take_back_votes.add(current_user.email_phone)
        else:                                         # if user pushed take_back button again
            take_back_votes.remove(current_user.email_phone)

        print('\ntake_back_votes :', take_back_votes)
        take_back_votes_count = len(take_back_votes)
        if (take_back_votes_count == 0) or (users_count == 0):
            take_back_percentage = ''
        elif take_back_votes_count / users_count >= (1/2) : # if more than 1/2 of users vote to take_back
            msg = language["are_you_agree_take_back"]
            show_modal('take_back', msg) # show a modal dialog on users page to ask them choose Yes or No for take_back method

        else:
            take_back_percentage = str(int(take_back_votes_count / users_count
                * 100)) + '%'

        emit('take_back_percentage', {'take_back_percentage':
            take_back_percentage}, broadcast=True)


def countdown_take_back_modal(t):
    """countdown timer for take_back modal dialog
    """
    global countdown_modal_on, agg_announce
    countdown_modal_on = True
    agg_announce == True # cancel countdown_aggregation
    print('\nmodal Timer ON')
    emit('countdown_modal', 30, broadcast=True) # countdown timer for modal poll for 30s
    for _ in range(t):
        if modal_announce == False:
            print('\nmodal Timer aborted')
            countdown_modal_on = False
            return
        else:
            time.sleep(1)

    countdown_modal_on = False
    print('\nmodal Timer OFF')

    # if timeout
    global take_back_percentage ,max_legal_moves, fen,\
        take_back_votes_count, take_back_votes, prevent_drag
    if votes.count('yes') >= 0.5 * len(votes): # if majority of current gathered votes is yes
        agg_announce = True
        emit('remove_recommend_choice', broadcast=True) # remove recommend_choice if any client has it
        votes.clear()
        print('take back')
        take_back() # consensus to do take_back
        fen, max_legal_moves = get_fen() # FEN of current game
        emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves}, broadcast=True) # force client to take_back
        emit('hide_modal', broadcast=True)
        prevent_drag = False
        emit('preventDrag', prevent_drag, broadcast=True)
        take_back_percentage = ''
        take_back_votes.clear()
        take_back_votes_count = 0
        emit('take_back_percentage', {'take_back_percentage':
            take_back_percentage}, broadcast=True)

def ack_take_back(vote):
    global take_back_percentage ,max_legal_moves, fen,\
        take_back_votes_count, take_back_votes, agg_announce, prevent_drag
    votes.append(vote)
    print(votes)

    if votes.count('yes') >= ((1/2) * users_count): # if majority of votes is yes
        agg_announce = True
        emit('remove_recommend_choice', broadcast=True) # remove recommend_choice if any client has it
        votes.clear()
        print('take back')
        take_back() # consensus to do take_back
        fen, max_legal_moves = get_fen() # FEN of current game
        emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves}, broadcast=True) # force client to take_back
        emit('hide_modal', broadcast=True)
        prevent_drag = False
        emit('preventDrag', prevent_drag, broadcast=True)
        take_back_percentage = ''
        take_back_votes.clear()
        take_back_votes_count = 0
        emit('take_back_percentage', {'take_back_percentage':
            take_back_percentage}, broadcast=True)

    elif votes.count('no') >= ((1/2) * users_count) or len(votes) == users_count:
        votes.clear()
        emit('hide_modal', broadcast=True)
        take_back_percentage = ''
        take_back_votes.clear()
        take_back_votes_count = 0
        emit('take_back_percentage', {'take_back_percentage':
            take_back_percentage}, broadcast=True)

    elif len(votes) >= ((1/2) * users_count) and not countdown_modal_on:
        countdown_take_back_modal(30) # wait for other users' choice for 30 second, then deside what to do


def countdown_new_game_modal(t):
    """countdown timer for new_game modal dialog
    """
    global countdown_modal_on, agg_announce
    countdown_modal_on = True
    agg_announce == True # cancel countdown_aggregation
    print('\nmodal Timer ON')
    emit('countdown_modal', 30, broadcast=True) # countdown timer for modal poll for 30s
    for _ in range(t):
        if modal_announce == False:
            print('\nmodal Timer aborted')
            countdown_modal_on = False
            return
        else:
            time.sleep(1)

    countdown_modal_on = False
    print('\nmodal Timer OFF')

    # if timeout
    global new_game_percentage ,max_legal_moves, fen,\
        new_game_votes_count, new_game_votes, prevent_drag
    if votes.count('yes') >= 0.5 * len(votes): # if majority of current gathered votes is yes
        agg_announce = True
        emit('remove_recommend_choice', broadcast=True) # remove recommend_choice if any client has it
        votes.clear()
        print('new game')
        new_game() # consensus to do new_game
        fen, max_legal_moves = get_fen() # FEN of current game
        emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves}, broadcast=True) # force client to new_game
        emit('hide_modal', broadcast=True)
        prevent_drag = False
        emit('preventDrag', prevent_drag, broadcast=True)
        new_game_percentage = ''
        new_game_votes.clear()
        new_game_votes_count = 0
        emit('new_game_percentage', {'new_game_percentage':
            new_game_percentage}, broadcast=True)

def ack_new_game(vote):
    global new_game_percentage ,max_legal_moves, fen,\
        new_game_votes_count, new_game_votes, agg_announce, prevent_drag
    votes.append(vote)
    print(votes)

    if votes.count('yes') >= ((1/2) * users_count): # if majority of votes is yes
        agg_announce = True
        emit('remove_recommend_choice', broadcast=True) # remove recommend_choice if any client has it
        votes.clear()
        print('new game')
        new_game() # consensus to do new_game
        fen, max_legal_moves = get_fen() # FEN of current game
        emit('update_client_interface', {'fen':fen,
            'max_legal_moves':max_legal_moves}, broadcast=True) # force client to new_game
        emit('hide_modal', broadcast=True)
        prevent_drag = False
        emit('preventDrag', prevent_drag, broadcast=True)
        new_game_percentage = ''
        new_game_votes.clear()
        new_game_votes_count = 0
        emit('new_game_percentage', {'new_game_percentage':
            new_game_percentage}, broadcast=True)

    elif votes.count('no') >= ((1/2) * users_count) or len(votes) == users_count:
        votes.clear()
        emit('hide_modal', broadcast=True)
        new_game_percentage = ''
        new_game_votes.clear()
        new_game_votes_count = 0
        emit('new_game_percentage', {'new_game_percentage':
            new_game_percentage}, broadcast=True)

    elif len(votes) >= ((1/2) * users_count) and not countdown_modal_on:
        countdown_new_game_modal(30) # wait for other users' choice for 30 second, then deside what to do

def show_modal(method, msg):
    """
    show a modal dialog on client side with a question to choose between
    'yes' or 'no'.
    return 'yes' or 'no' if half of users choose any.
    if in a period of time half of answers are not same, default is 'no'.
    """
    if method == 'take_back':
        emit('show_modal', msg, broadcast=True, callback=ack_take_back)
    elif method == 'new_game':
        emit('show_modal', msg, broadcast=True, callback=ack_new_game)