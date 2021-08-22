# this is aggregator for CrowdChess project
from flask import Flask
from flask import Blueprint, render_template, flash
from flask.globals import request
from flask_login import login_required, current_user
from flask_socketio import emit
from __init__ import socketio


# aggregator blueprint
aggregator = Blueprint('aggregator', __name__)

connected_users = set() # currently connected users to server
online_users = set() # users present on users.html page

@socketio.on('connect')
def on_connect(auth):
    online_users.add(current_user.email)
    users_count = len(online_users)
    emit('connected users', {'users_count' : users_count}, broadcast=True)
    print('\n', current_user.name, current_user.email, ' connected\n')

@socketio.on('disconnect')
def test_disconnect():
    online_users.remove(current_user.email)
    users_count = len(online_users)
    emit('connected users', {'users_count' : users_count}, broadcast=True)
    print('Client disconnected: ', current_user.name)

@socketio.on('connect', namespace='/users')
def on_connect(auth):
    online_users.add(current_user.email)
    users_count = len(online_users)
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)

@socketio.on('disconnect', namespace='/users')
def test_disconnect():
    online_users.remove(current_user.email)
    users_count = len(online_users)
    emit('on_main_page_users', {'users_count' : users_count}, broadcast=True)