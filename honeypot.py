#!/usr/bin/env python

import sqlite3
import sys
import os

import flask
import flask.ext.login as flask_login

import config


class User(flask_login.UserMixin):
    pass


def create_database(db):
    # db.execute("CREATE TABLE")
    print("Empty")


def main():
    print(os.getcwd())
    app = flask.Flask(__name__)

    app.secret_key = config.secret_key
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    @app.route('/')
    def root():
        return flask.send_from_directory('static', 'index.html')

    @app.route('/<path:filename>')
    def catch_all(filename):
        return flask.send_from_directory('static', filename)

    @login_manager.user_loader  # should create user object (get from database etc)
    def user_loader(username):
        print("=== user_loader ===")
        userdb = get_db().execute("SELECT * FROM users WHERE username='" + username + "'")
        if userdb is None:
            return

        user = User()
        user.username = username
        user.role = userdb.fetchone()[2]
        return user

    @login_manager.request_loader  # gets called when unauthorized, additional authorization methods
    def request_loader(request):
        print("=== request_loader ===")
        print(request.method + " - " + request.remote_addr)
        return None

    @login_manager.unauthorized_handler
    def unauthorized_handler():
        return flask.Response("{\"status\": \"error\", \"error_message\": \"Not authorized.\"}",
                              mimetype="application/json")

    # ACTUAL METHOD
    # ssl_context = ('server.crt', 'server.key')
    try:
        app.run(host='0.0.0.0',
                port=5000,
                # ssl_context=ssl_context,
                debug=config.debug)
    except OSError as err:
        print("[ERROR] " + err.strerror, file=sys.stderr)
        print("[ERROR] The program will now terminate.", file=sys.stderr)


def get_db():
    if not hasattr(flask.g, 'sqlite_db'):
        flask.g.sqlite_db = sqlite3.connect("honeypot.sqlite")
    return flask.g.sqlite_db


if __name__ == '__main__':
    main()
