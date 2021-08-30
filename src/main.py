from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from flask_socketio import emit
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

@socketio.on('connect')
def on_connect(auth):
    online_users.add(request.sid)
    users_count = len(online_users)
    emit('connected users', {'users_count' : users_count}, broadcast=True)
    #print('\n', current_user.name, current_user.email, ' connected\n')

@socketio.on('disconnect')
def test_disconnect():
    online_users.remove(request.sid)
    users_count = len(online_users)
    emit('connected users', {'users_count' : users_count}, broadcast=True)
    #print('Client disconnected: ', current_user.name)


app = create_app(debug=True) # initialize flask app using the __init__.py function
if __name__ == '__main__':
    socketio.run(app)