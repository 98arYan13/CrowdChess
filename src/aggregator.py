# this is aggregator for CrowdChess project
from flask import Flask
from flask import Blueprint, render_template, flash
from flask.globals import request
from flask_login import login_required, current_user
from flask_socketio import emit
from __init__ import socketio


# aggregator blueprint
aggregator = Blueprint('aggregator', __name__)


"""# number of connected users to server
def user_count(signal, n=[0]):
    if signal:
        n[0] += 1
    else:
        n[0] -= 1
    return n[0]


@aggregator.route('/user_signal', methods=['POST'])
def user_signal():
    signal = request.form.get("connection_status")
    counter = user_count(signal)
    print('counter: ', counter)
    return {'total_online_users': counter}"""

connected_users = set() # currently connected users to server
online_users = set() # users present on users.html page

@socketio.on('connect', namespace='/users')
def on_connect(auth):
    online_users.add(current_user.email)
    users_count = len(online_users)
    emit('online users', {'users_count' : users_count}, broadcast=True)
    print('\n', current_user.name, current_user.email, ' connected\n')

@socketio.on('disconnect', namespace='/users')
def test_disconnect():
    online_users.remove(current_user.email)
    users_count = len(online_users)
    emit('online users', {'users_count' : users_count}, broadcast=True)
    print('Client disconnected: ', current_user.name)