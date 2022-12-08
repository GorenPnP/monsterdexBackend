FROM python:3.8-slim-buster

# set work directory
WORKDIR /usr/src/monsterdex-backend

# COPY requirements.txt requirements.txt
COPY . .
RUN pip3 install -r requirements.txt

ENV FLASK_APP=app/app.py
ENV FLASK_ENV=production

WORKDIR /usr/src/monsterdex-backend/app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]