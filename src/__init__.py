# Initialize app


import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import config
import json


# creating "datas" folder if there isn't any
try:
    os.mkdir("./datas")
except OSError as e:
    print(e)
    pass


default_language = config.app_default_language

# load defualt language json file
with open("./language/" + default_language + ".json", 'r',
    encoding='utf8') as file:
        language = json.loads(file.read())


db = SQLAlchemy()
login_manager = LoginManager()

socketio = SocketIO(
    engineio_logger=config.engineio_logger,
    logger=config.logger,
    async_mode = 'threading'
)

limiter = Limiter(
    key_func=get_remote_address,
)

def create_app(debug=False):

    app = Flask(__name__)

    app.config.update(SECRET_KEY=config.SECRET_KEY)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datas/db.sqlite' # it is the path where the SQLite database file will be saved
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # deactivate Flask-SQLAlchemy track modifications
    app.debug = debug

    # Initialize Plugins
    db.init_app(app) # Initialiaze sqlite database

    login_manager = LoginManager() # TODO: delete this line
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app) # configure it for login

    limiter.init_app(app) # initialize limiter

    from models import User
    @login_manager.user_loader
    def load_user(user_id): #reload user object from the user ID stored in the session
        return User.query.get(int(user_id))

    # blueprint for auth routes
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    # blueprint for non-auth parts of app
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # blueprint for chess processes CrowdChess (ches.py)
    from ches import ches as ches_blueprint
    app.register_blueprint(ches_blueprint)

    # blueprint for aggregator for CrowdChess project (aggregator)
    from aggregator import aggregator as aggregator_blueprint
    app.register_blueprint(aggregator_blueprint)

    socketio.init_app(app)

    return app


db.create_all(app=create_app()) # create the SQLite database