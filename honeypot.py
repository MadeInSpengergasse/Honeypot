#!/usr/bin/env python

import sqlite3
import sys
import json
import requests
import flask
import flask.ext.login as flask_login

import config

GITHUB_ACCESS_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"


class User(flask_login.UserMixin):
    pass


def create_database():
    print("Creating database (if not exists).")
    db = sqlite3.connect("honeypot.sqlite")
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(20),
            name VARCHAR(100),
            access_token VARCHAR(30),
            PRIMARY KEY (id)
        )
    """)
    db.commit()
    db.close()


def main():
    app = flask.Flask(__name__)

    app.secret_key = config.secret_key
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    create_database()

    @app.route('/')
    def root():
        return flask.send_from_directory('static', 'index.html')

    @app.route('/api/github_callback', methods=['GET'])
    def github_callback():
        payload = {"client_id": config.github_client_id,
                   "client_secret": config.github_client_secret,
                   "code": flask.request.args.get("code"),
                   "accept": "json"}
        header = {"Accept": "application/json"}

        response = requests.post(GITHUB_ACCESS_TOKEN, data=payload, headers=header)

        json_resp = response.json()
        if json_resp.get("error") == "bad_verification_code":
            return "Bad verification code."
        if json_resp.get("scope") != "user:email":
            return "Scope wrong."
        access_token = json_resp.get("access_token")
        payload = {"access_token": access_token}
        response = requests.get(GITHUB_USER, params=payload)
        json_resp = response.json()

        user = User()
        user.access_token = access_token
        user.id = str(json_resp.get("id"))
        user.name = json_resp.get("name")
        flask_login.login_user(user)

        userexists = len(get_db().execute("SELECT id FROM users WHERE id='" + user.id + "'").fetchall()) != 0
        if not userexists:
            print("Creating user")
            get_db().execute("INSERT INTO users (name, id, access_token) VALUES ('" + user.name + "', '"+user.id+"', '"+user.access_token+"')")
            get_db().commit()
        else:
            print("User exists.")
        return flask.redirect("/")

    @app.route('/api/logout', methods=['GET', 'POST'])
    def logout():
        flask_login.logout_user()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")

    @app.route('/api/get_client_id', methods=['GET'])
    def get_client_id():
        return flask.Response(config.github_client_id, mimetype="text/plain")

    @app.route('/api/get_user_info', methods=['GET'])
    @flask_login.login_required
    def get_user_info():
        ret_obj = {"status": "ok", "user": flask_login.current_user.__dict__}
        return flask.Response(json.dumps(ret_obj), mimetype="application/json")

    @app.route('/<path:filename>')
    def catch_all(filename):
        return flask.send_from_directory('static', filename)

    @login_manager.user_loader  # should create user object (get from database etc), called when user object is needed
    def user_loader(id):
        print("=== user_loader ===")
        userdb = get_db().execute("SELECT * FROM users WHERE id='" + id + "'")
        if userdb is None:
            return
        user_obj = userdb.fetchone()
        user = User()
        user.name = user_obj[0]
        user.id = user_obj[1]
        user.access_token = user_obj[2]

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
        print("[ERROR] The program w ill now terminate.", file=sys.stderr)


def get_db():
    if not hasattr(flask.g, 'sqlite_db'):
        flask.g.sqlite_db = sqlite3.connect("honeypot.sqlite")
    return flask.g.sqlite_db


if __name__ == '__main__':
    main()
