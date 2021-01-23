#! /bin/bash
cd ~/Schreibtisch/monsterBackend/venv

source ./bin/activate
pip3 install -r requirements.txt
export FLASK_APP=app/app.py
export FLASK_ENV=development
code .

flask run
