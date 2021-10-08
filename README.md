# CrowdChess
This is crowdchess project.

## Sources used:
https://hackersandslackers.com/flask-login-user-authentication/

https://github.com/maksimKorzh/uci-gui

## Setup

```
cd src
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

```
mv config.py.sample config.py
```

Edit `config.py`. Create a secret key for managing sessions.

## Running
```py main.py```
