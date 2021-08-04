from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from __init__ import create_app, db, socketio


# main blueprint
main = Blueprint('main', __name__)

import  events

@main.route('/') # home page that return 'index'
@login_required
def index():
    return render_template('users.html')

@main.route('/profile') # profile page that return 'profile'
@login_required
def profile():
    return render_template('profile.html', name=current_user.name)

app = create_app(debug=True) # initialize flask app using the __init__.py function
if __name__ == '__main__':
    db.create_all(app=create_app()) # create the SQLite database
    socketio.run(app)