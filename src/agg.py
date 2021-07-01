# This (agg.py) is for connecting peaple to each other and the system
# and will aggregate all choices to elicit an outcome as the crowd answer for
# next chess move.
from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello():
    return "This is for test"