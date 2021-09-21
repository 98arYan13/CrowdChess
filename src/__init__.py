# Initialize app


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import config
from flask_socketio import SocketIO


db = SQLAlchemy()
login_manager = LoginManager()

# socketio
socketio = SocketIO(engineio_logger=config.engineio_logger, logger=config.logger,
                    async_mode = 'threading')

def create_app(debug=False):
    # Construct the core app object
    app = Flask(__name__)

    # Application Configuration
    app.config.update(SECRET_KEY=config.SECRET_KEY)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///datas/db.sqlite' # it is the path where the SQLite database file will be saved
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # deactivate Flask-SQLAlchemy track modifications
    app.debug = debug

    # Initialize Plugins
    db.init_app(app) # Initialiaze sqlite database
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app) # configure it for login

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