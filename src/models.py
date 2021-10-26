from __init__ import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    # User account model

    __tablename__ = 'flasklogin-users'
    id = db.Column(
        db.Integer,
        primary_key=True # primary keys are required by SQLAlchemy
    )
    name = db.Column(
        db.String(100),
        nullable=False,
        unique=False
    )
    email_phone = db.Column(
        db.String(40),
        unique=True,
        nullable=False
    )
    password = db.Column(
        db.String(200),
        primary_key=False,
        unique=False,
        nullable=False
	)