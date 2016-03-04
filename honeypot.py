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
    #     print(db.execute("""
    # SELECT t.t_id, t.t_title, t.t_description, t.t_u_asignee, t.t_m_milestone, t.t_status,
    # (SELECT ts.ts_timestamp FROM timestamp ts WHERE ts.ts_id=t.t_ts_created) AS created,
    # (SELECT u.u_name FROM users u WHERE u.u_id=ts.ts_u_id AND t.t_ts_created=ts.ts_id) AS createdby,
    # (SELECT ts.ts_timestamp FROM timestamp ts WHERE ts.ts_id=t.t_ts_closed) AS closed,
    # (SELECT u.u_name FROM users u WHERE u.u_id=ts.ts_u_id AND t.t_ts_closed=ts.ts_id) AS closedby,
    # t.t_p_project
    # FROM todo t, timestamp ts where t.t_id=?
    #     """).fetchall()[0])
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
        print(json_resp)
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
        # lastrow = get_db().execute("INSERT INTO timestamp (ts_u_id) VALUES (?)",
        #                            (flask_login.current_user.id,)).lastrowid
        id = get_db().execute(
            "INSERT INTO todo (t_title, t_description, t_u_asignee, t_m_milestone, t_status, t_p_project) VALUES (?, ?, ?, ?, ?, ?)",
            (params.get("title"), params.get("description"), params.get("asignee"), params.get("milestone"), 0,
             params.get("project_id"))).lastrowid
        get_db().execute("INSERT INTO event (e_type, e_u_id, e_t_id) VALUES (?, ?, ?)",
                         (0, flask_login.current_user.id, id))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\", \"id\": \"" + str(id) + "\"}", mimetype="application/json")

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
        id = get_db().execute("INSERT INTO project (p_title, p_description, p_status) VALUES (?, ?, 0)",
                              (flask.request.json.get("title"), flask.request.json.get("description"))).lastrowid
        get_db().commit()
        # flask.request.json.get("title")
        # flask.request.json.get("description")
        return flask.Response("{\"status\": \"ok\", \"id\": " + str(id) + "}", mimetype="application/json")
        # return "Not implemented."
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
        timestamps = get_db().execute("SELECT t_ts_created, t_ts_closed FROM todo WHERE t_id=?",
                                      (flask.request.json.get("id"),)).fetchall()
        if not timestamps:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Unknown id.\"}",
                                  mimetype="application/json")
        get_db().execute("DELETE FROM timestamp WHERE ts_id IN (?, ?)", timestamps[0])
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

    @app.route('/api/get_todo_detail', methods=['GET'])
    @flask_login.login_required
    def get_details():
        # response = get_db().execute("""
        #     SELECT t.t_id, t.t_title, t.t_description, t.t_u_asignee, t.t_m_milestone, t.t_status,
        #     (SELECT ts.ts_timestamp FROM timestamp ts WHERE ts.ts_id=t.t_ts_created) AS created,
        #     (SELECT u.u_name FROM users u WHERE u.u_id=ts.ts_u_id AND t.t_ts_created=ts.ts_id) AS createdby,
        #     (SELECT ts.ts_timestamp FROM timestamp ts WHERE ts.ts_id=t.t_ts_closed) AS closed,
        #     (SELECT u.u_name FROM users u WHERE u.u_id=ts.ts_u_id AND t.t_ts_closed=ts.ts_id) AS closedby,
        #     t.t_p_project
        #     FROM todo t, timestamp ts WHERE t.t_id=?
        # """, (flask.request.args.get("id"),)).fetchone()
        response = get_db().execute(
            "SELECT t.t_id, t.t_title, t.t_description, t.t_u_asignee, t.t_m_milestone, t.t_status FROM todo t, timestamp ts WHERE t.t_id=?",
            (flask.request.args.get("id"),)).fetchone()
        # ret = {"id": response[0], "title": response[1], "description": response[2], "asignee": response[3],
        #        "milestone": response[4], "status": response[5], "created": response[6], "createdby": response[7],
        #        "closed": response[8], "closedby": response[9]}
        if response is None:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        ret = {"id": response[0], "title": response[1], "description": response[2], "asignee": response[3],
               "milestone": response[4], "status": response[5]}
        return flask.Response(json.dumps(ret), mimetype="application/json")
        # return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
        #                       mimetype="application/json")

    @app.route('/api/get_todos', methods=['GET'])
    @flask_login.login_required
    def get_todo_details():
        project_id = flask.request.args.get("project_id")
        milestone_id = flask.request.args.get("milestone_id")
        if project_id is not None:
            result = get_db().execute("SELECT t_id, t_title, t_description, t_status FROM todo WHERE t_p_project=?",
                                      (project_id,)).fetchall()
        elif milestone_id is not None:
            result = get_db().execute("SELECT t_id, t_title, t_description, t_status FROM todo WHERE t_m_milestone=?",
                                      (milestone_id,)).fetchall()
        else:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        ret = []
        for a in result:  # TODO: Return better timestamp things
            ret.append({"id": a[0], "title": a[1], "description": a[2], "status": a[3]})
        return json.dumps(ret)
        # TODO: Test

    @app.route('/api/get_milestones', methods=['GET'])
    @flask_login.login_required
    def get_milestones():
        result = get_db().execute("SELECT m_id, m_title, m_status FROM milestone WHERE m_p_project=?",
                                  (flask.request.args.get("project_id"),)).fetchall()
        print(result)
        ret = []
        for a in result:
            ret.append(
                {"id": a[0], "title": a[1], "status": a[2]})
        return json.dumps(ret)

    @app.route('/api/get_milestone', methods=['GET'])
    @flask_login.login_required
    def get_milestone():
        result = get_db().execute(
            "SELECT m_title, m_description, m_starttime, m_endtime, m_status FROM milestone WHERE m_id=?",
            (flask.request.args.get("milestone_id"),)).fetchone()
        if not result:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        return json.dumps({"title": result[0], "description": result[1], "starttime": result[2], "endtime": result[3],
                           "status": result[4]})

    @app.route('/api/get_projects', methods=['GET'])
    @flask_login.login_required
    def get_projects():
        res = get_db().execute("SELECT p_id, p_title, p_description, p_status FROM project").fetchall()
        ret = []
        for tupl in res:
            ret.append({"id": tupl[0], "title": tupl[1], "description": tupl[2], "status": tupl[3]})
        return json.dumps(ret)

    @app.route('/api/get_project', methods=['GET'])
    @flask_login.login_required
    def get_project():
        res = get_db().execute("SELECT p_id, p_title, p_description, p_status FROM project WHERE p_id=?",
                               (flask.request.args.get("project_id"),)).fetchone()
        if res is None:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        ret = {"id": res[0], "title": res[1], "description": res[2], "status": res[3]}
        return json.dumps(ret)

    @app.route('/api/get_users', methods=['GET'])
    @flask_login.login_required
    def get_users():
        if not flask.request.args.get("name"):
            search = "%"
        else:
            search = "%" + flask.request.args.get("name") + "%"
        res = get_db().execute("SELECT u_id, u_name FROM users WHERE u_name LIKE ? COLLATE nocase",
                               (search,)).fetchall()
        ret = []
        for tupl in res:
            ret.append({"id": tupl[0], "name": tupl[1]})
        return json.dumps(ret)

    # -------------------------- OTHER --------------------------

    @app.route('/<path:filename>')
    def catch_all(filename):
        return flask.send_from_directory('static', filename)

    @login_manager.user_loader  # should create user object (get from database etc), called when user object is needed
    def user_loader(user_id):
        print("=== user_loader ===")
        userdb = get_db().execute("SELECT u_id, u_name FROM users WHERE u_id=?", (user_id,))
        if userdb is None:
            return
        user_obj = userdb.fetchone()
        user = User()
        user.id = user_obj[0]
        user.name = user_obj[1]

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
