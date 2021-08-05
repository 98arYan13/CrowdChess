# this is aggregator for CrowdChess project
from flask import Flask
from flask import Blueprint, render_template, flash
from flask.globals import request
from flask_login import login_required, current_user


# aggregator blueprint
aggregator = Blueprint('aggregator', __name__)


# number of connected users to server
def user_count(signal, n=[0]):
    if signal:
        n[0] += 1
    else:
        n[0] -= 1
    return n[0]


@aggregator.route('/user_signal', methods=['POST'])
def user_signal():
    signal = request.form.get("connection_status")
    counter = user_count(signal)
    print('counter: ', counter)
    return {'total_online_users': counter}