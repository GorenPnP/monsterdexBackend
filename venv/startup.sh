#! /bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
cd $SCRIPTPATH && \

source ./bin/activate && \
pip3 install -r requirements.txt && \
export FLASK_APP=app/app.py && \
export FLASK_ENV=development && \

flask run
