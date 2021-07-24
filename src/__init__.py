# Initialize app
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import config


db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    # Construct the core app object
    app = Flask(__name__)

    # Application Configuration
    app.config.update(SECRET_KEY=config.SECRET_KEY)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite' # it is the path where the SQLite database file will be saved
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # deactivate Flask-SQLAlchemy track modifications

    # Initialize Plugins
    db.init_app(app) # Initialiaze sqlite database
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app) # configure it for login

    from models import User
    @login_manager.user_loader
    def load_user(user_id): #reload user object from the user ID stored in the session
        # since the user_id is just the primary key of our user table, use it in the query for the user
        return User.query.get(int(user_id))
    
    # blueprint for auth routes
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    # blueprint for non-auth parts of app
    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app