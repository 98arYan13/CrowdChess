import functools
from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from flask_socketio import disconnect, emit, send
from __init__ import create_app, socketio


# main blueprint
main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('users.html')

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)


online_users = set() # currently connected users to server

# Using Flask-Login with Flask-SocketIO
def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

@socketio.on('connect')
@authenticated_only
def on_connect(auth):
    online_users.add(current_user.email)
    users_count = len(online_users)
    emit('connected users', {'users_count' : users_count}, broadcast=True)
    print('\n', current_user.name, current_user.email, ' connected\n')

@socketio.on('disconnect')
@authenticated_only
def test_disconnect():
    online_users.remove(current_user.email)
    users_count = len(online_users)
    emit('connected users', {'users_count' : users_count}, broadcast=True)
    print('Client disconnected: ', current_user.name)


"""

@socketio.on('my event')
@authenticated_only
def handle_my_custom_event(data):
    print('Client connected: {.name}.'.format(current_user))
    emit('my response', {'message': '{0} has joined'.format(current_user.name)},
         broadcast=True)


@socketio.on('message from user', namespace='/messages')
def receive_message_from_user(message):
    print('USER MESSAGE: {}'.format(message))
    emit('from flask', message.upper(), broadcast=True)


@socketio.on('message')
def receive_message(message):
    print('########: {}'.format(message))
    send('This is a message from Flask.')"""


app = create_app(debug=True) # initialize flask app using the __init__.py function
if __name__ == '__main__':
    socketio.run(app)