import functools
from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from flask_socketio import disconnect, emit, send
from __init__ import create_app, db, socketio


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


# Using Flask-Login with Flask-SocketIO
def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped

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

@socketio.on('connect')
def on_connect():
    print('xxxxxxxxxxxxxxx')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)

@socketio.on('message')
def receive_message(message):
    print('########: {}'.format(message))
    send('This is a message from Flask.')


app = create_app(debug=True) # initialize flask app using the __init__.py function
if __name__ == '__main__':
    socketio.run(app)