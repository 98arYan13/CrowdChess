import functools
from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from __init__ import create_app, db, socketio
from flask_socketio import disconnect, emit



# main blueprint
main = Blueprint('main', __name__)


@main.route('/') # home page that return 'index'
@login_required
def index():
    return render_template('users.html')


@main.route('/profile') # profile page that return 'profile'
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

# TODO: seems frontend don't call this code, then ignored it for now.
"""# Using Flask-Login with Flask-SocketIO
# https://flask-socketio.readthedocs.org/en/latest/
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
         broadcast=True)"""


app = create_app(debug=True) # initialize flask app using the __init__.py function
if __name__ == '__main__':
    db.create_all(app=create_app()) # create the SQLite database
    socketio.run(app)