from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_socketio import Namespace, emit
from __init__ import socketio



@socketio.on('connect')
def connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def disconnect():
    print('Client disconnected')
