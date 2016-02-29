#!/usr/bin/env python

import sqlite3
import sys
import json
import requests
import flask
import flask.ext.login as flask_login

import config

GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"


class User(flask_login.UserMixin):
    pass


def create_database():
    print("Creating database (if not exists).")
    db = sqlite3.connect("honeypot.sqlite")
    db.executescript(open("create_database.sql", "r").read())
    db.commit()
    db.close()


def main():
    app = flask.Flask(__name__)

    app.secret_key = config.secret_key
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    @app.route('/')
    def root():
        return flask.send_from_directory('static', 'index.html')

    # -------------------------- GENERAL --------------------------

    @app.route('/api/github_callback', methods=['GET'])
    def github_callback():
        payload = {"client_id": config.github_client_id,
                   "client_secret": config.github_client_secret,
                   "code": flask.request.args.get("code"),
                   "accept": "json"}
        header = {"Accept": "application/json"}

        response = requests.post(GITHUB_ACCESS_TOKEN_URL, data=payload, headers=header)

        json_resp = response.json()
        if json_resp.get("error") == "bad_verification_code":
            return "Bad verification code."
        if json_resp.get("scope") != "user:email":
            return "Scope wrong."
        access_token = json_resp.get("access_token")
        payload = {"access_token": access_token}
        response = requests.get(GITHUB_USER, params=payload)
        json_resp = response.json()
        print(response.text)
        user = User()
        user.access_token = access_token
        user.id = str(json_resp.get("id"))
        user.name = json_resp.get("login")
        flask_login.login_user(user)

        userexists = len(get_db().execute("SELECT u_id FROM users WHERE u_id = ?", (user.id,)).fetchall()) != 0
        if not userexists:
            print("Creating user")
            get_db().execute(
                "INSERT INTO users (u_name, u_id, u_access_token) VALUES (?, ?, ?)",
                (user.name, user.id, user.access_token))
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
    def get_user_info():  # TODO: dont expose access_token (should it be private?)
        ret_obj = {"status": "ok", "user": flask_login.current_user.__dict__}
        return flask.Response(json.dumps(ret_obj), mimetype="application/json")

    # -------------------------- ADD --------------------------

    @app.route('/api/add_todo', methods=['POST'])
    @flask_login.login_required
    def add_todo():
        params = flask.request.json
        lastrow = get_db().execute("INSERT INTO timestamp (ts_u_id) VALUES (?)",
                                   (flask_login.current_user.id,)).lastrowid
        get_db().execute(
            "INSERT INTO todo (t_title, t_description, t_u_asignee, t_m_milestone, t_status, t_ts_created) VALUES (?, ?, ? , ?, ?, ?)",
            (params.get("title"), params.get("description"), params.get("asignee"), params.get("milestone"), 0,
             lastrow))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")

    @app.route('/api/add_label', methods=['POST'])
    @flask_login.login_required
    def add_label():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/add_milestone', methods=['POST'])
    @flask_login.login_required
    def add_milestone():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/add_project', methods=['POST'])
    @flask_login.login_required
    def add_project():
        return "Not implemented."
        # TODO: Implement

    # -------------------------- UPDATE --------------------------

    @app.route('/api/update_todo', methods=['POST'])
    @flask_login.login_required
    def update_todo():
        params = flask.request.json
        if params.get("status") == 1:  # close todo
            lastrow = get_db().execute("INSERT INTO timestamp (ts_u_id) VALUES (?)",
                                       (flask_login.current_user.id,)).lastrowid
        elif params.get("status") == 0:
            lastrow = None
        else:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Invalid status.\"}",
                                  mimetype="application/json")
        get_db().execute(
            "UPDATE todo SET t_title=?, t_description=?, t_u_asignee=?, t_m_milestone=?, t_status=?, t_ts_closed=? WHERE t_id=?",
            (params.get("title"), params.get("description"), params.get("asignee"), params.get("milestone"),
             params.get("status"), lastrow, params.get("id")))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/update_label', methods=['POST'])
    @flask_login.login_required
    def update_label():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/update_milestone', methods=['POST'])
    @flask_login.login_required
    def update_milestone():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/update_project', methods=['POST'])
    @flask_login.login_required
    def update_project():
        return "Not implemented."
        # TODO: Implement

    # -------------------------- REMOVE --------------------------

    @app.route('/api/remove_todo', methods=['POST'])
    @flask_login.login_required
    def remove_todo():
        rowcount = get_db().execute("DELETE FROM todo WHERE t_id=?", (flask.request.json.get("id"),)).rowcount
        get_db().commit()
        if rowcount != 1:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Unknown id.\"}",
                                  mimetype="application/json")
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/remove_label', methods=['POST'])
    @flask_login.login_required
    def remove_label():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/remove_milestone', methods=['POST'])
    @flask_login.login_required
    def remove_milestone():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/remove_project', methods=['POST'])
    @flask_login.login_required
    def remove_project():
        return "Not implemented."
        # TODO: Implement

    # -------------------------- GET --------------------------

    @app.route('/api/get_todo_details', methods=['GET'])
    @flask_login.login_required
    def get_details():
        response = get_db().execute("SELECT * FROM todo WHERE t_id=?", (flask.request.args.get("id"),)).fetchone()
        if response is not None:
            # TODO: also return date and user for timestamps (subselects)
            time_response = get_db().execute("SELECT * FROM timestamp WHERE ts_id IN (?, ?)",
                                             (response[6], response[7])).fetchall()
            ret = {"id": response[0], "title": response[1], "description": response[2], "asignee": response[3],
                   "milestone": response[4], "status": response[5], "created": "TODO", "createdby": "TODO",
                   "closed": "TODO", "closedby": "TODO"}
            return flask.Response(json.dumps(ret), mimetype="application/json")
        return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                              mimetype="application/json")

    @app.route('/api/get_todos', methods=['GET'])
    @flask_login.login_required
    def get_todo_details():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/get_milestones', methods=['GET'])
    @flask_login.login_required
    def get_milestones():
        return "Not implemented."
        # TODO: Implement

    @app.route('/api/get_projects', methods=['GET'])
    @flask_login.login_required
    def get_projects():
        res = get_db().execute("SELECT p_id, p_title, p_status FROM project").fetchall()
        return "Not implemented."
        # TODO: Implement

    # -------------------------- OTHER --------------------------

    @app.route('/<path:filename>')
    def catch_all(filename):
        return flask.send_from_directory('static', filename)

    @login_manager.user_loader  # should create user object (get from database etc), called when user object is needed
    def user_loader(id):
        print("=== user_loader ===")
        userdb = get_db().execute("SELECT * FROM users WHERE u_id=?", (id,))
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
        print("[ERROR] The program will now terminate.", file=sys.stderr)


def get_db():
    if not hasattr(flask.g, 'sqlite_db'):
        flask.g.sqlite_db = sqlite3.connect("honeypot.sqlite")
    return flask.g.sqlite_db


if __name__ == '__main__':
    create_database()
    main()

    # db.execute("""
    #     CREATE TABLE IF NOT EXISTS users (
    #         id TEXT,
    #         name TEXT,
    #         access_token TEXT,
    #         PRIMARY KEY (id)
    #     )
    # """)
    # db.execute("""
    #     CREATE TABLE IF NOT EXISTS todo (
    #         t_id            INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    #         t_title         TEXT NOT NULL,
    #         t_description   TEXT NOT NULL,
    #         t_u_asignee     INTEGER,
    #         t_m_milestone   INTEGER,
    #         t_status        INTEGER NOT NULL,
    #         t_p_project     INTEGER NOT NULL,
    #         t_ts_created    INTEGER NOT NULL,
    #         t_ts_closed     INTEGER
    #     );
    # """)
    # db.execute("""
    #     CREATE TABLE IF NOT EXISTS timestamp (
    #         ts_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    #         ts_u_id INTEGER NOT NULL,
    #         ts_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    #     )
    # """)
