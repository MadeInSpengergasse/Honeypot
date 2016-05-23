#!/usr/bin/env python

import sqlite3
import sys
import json
import requests
import re
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
        print(json_resp)
        flask_login.login_user(user)

        userexists = len(get_db().execute("SELECT u_id FROM user WHERE u_id = ?", (user.id,)).fetchall()) != 0
        if not userexists:
            print("Creating user")
            get_db().execute(
                "INSERT INTO user (u_name, u_id, u_access_token, u_access_level) VALUES (?, ?, ?, ?)",
                (user.name, user.id, user.access_token, 1))
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

    # -------------------------- ADD --------------------------

    @app.route('/api/add_todo', methods=['POST'])
    @flask_login.login_required
    def add_todo():
        # TODO: Validation
        # Adds a todo from the given parameters
        params = flask.request.json
        if params.get("title") is None or params.get("project_id") is None:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Missing title or project_id.\"}",
                                  mimetype="application/json")
        todo_id = get_db().execute(
            "INSERT INTO todo (t_title, t_description, t_u_asignee, t_m_milestone, t_status, t_p_project) VALUES (?, ?, ?, ?, ?, ?)",
            (params.get("title"), params.get("description"), params.get("asignee"), params.get("milestone"), 0,
             params.get("project_id"))).lastrowid
        get_db().execute("INSERT INTO event (e_type, e_u_id, e_t_id) VALUES (?, ?, ?)",
                         (0, flask_login.current_user.id, todo_id))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\", \"id\": \"" + str(todo_id) + "\"}", mimetype="application/json")

    @app.route('/api/add_label', methods=['POST'])
    @flask_login.login_required
    def add_label():
        # TODO: Validation
        # Inserts label.
        if flask.request.json.get("name") is None or flask.request.json.get("color") is None:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Missing name or color.\"}",
                                  mimetype="application/json")
        color = flask.request.json.get("color")
        # match valid css color ("#" + 3 hex digits or "#" + 6 hex digits)
        match = re.match("^#(?:(?:[0-9A-F]{6})|(?:[0-9A-F]{3}))$", color, re.IGNORECASE)
        if not match:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Invalid color.\"}",
                                  mimetype="application/json")
        id = get_db().execute("INSERT INTO label (l_name, l_color) VALUES (?, ?)",
                              (flask.request.json.get("name"), flask.request.json.get("color"))).lastrowid
        get_db().commit()
        return flask.Response("{\"status\": \"ok\", \"id\": " + str(id) + "}", mimetype="application/json")

    @app.route('/api/add_milestone', methods=['POST'])
    @flask_login.login_required
    def add_milestone():
        # TODO: Validation
        # Insert a milestone
        params = flask.request.json
        id = get_db().execute(
            "INSERT INTO milestone (m_title, m_description, m_duedate, m_p_project, m_status) VALUES (?, ?, ?, ?, ?)",
            (params.get("title"), params.get("description"), params.get("duedate"),
             params.get("project_id"), 0)).lastrowid
        get_db().commit()
        return flask.Response("{\"status\": \"ok\", \"id\": \"" + str(id) + "\"}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/add_project', methods=['POST'])
    @flask_login.login_required
    def add_project():
        # TODO: Validation
        # Insert a project.
        id = get_db().execute("INSERT INTO project (p_title, p_description, p_status) VALUES (?, ?, 0)",
                              (flask.request.json.get("title"), flask.request.json.get("description"))).lastrowid
        get_db().commit()
        return flask.Response("{\"status\": \"ok\", \"id\": " + str(id) + "}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/add_comment', methods=['POST'])
    @flask_login.login_required
    def add_comment():
        # TODO: Validation
        # Add new event with comment & content and return details of that.
        last = get_db().execute("INSERT INTO event (e_type, e_content, e_t_id, e_u_id) VALUES (?, ?, ?, ?)", (
            2, flask.request.json.get("content"), flask.request.json.get("todo_id"),
            flask_login.current_user.id)).lastrowid
        get_db().commit()
        res = get_db().execute("SELECT e_type, e_u_id, e_content, e_timestamp FROM event WHERE e_id=?",
                               (last,)).fetchone()
        return flask.Response("{\"status\": \"ok\", \"new_comment\": " + json.dumps(
            {"type": res[0], "user": res[1], "content": res[2], "timestamp": res[3]}) + "}",
                              mimetype="application/json")

    @app.route('/api/add_label_to_todo', methods=['POST'])
    @flask_login.login_required
    def add_label_to_todo():
        # TODO: Validation
        # Insert into todo_and_label with label & todo id
        label_id = flask.request.json.get("label_id")
        todo_id = flask.request.json.get("todo_id")
        get_db().execute("INSERT INTO todo_and_label (tl_t_todo, tl_l_label) VALUES (?, ?)", (todo_id, label_id))
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")

    # -------------------------- UPDATE --------------------------

    @app.route('/api/update_todo', methods=['POST'])
    @flask_login.login_required
    def update_todo():
        # TODO: Validation
        # Update values in db
        params = flask.request.json
        get_db().execute(
            "UPDATE todo SET t_title=?, t_description=?, t_u_asignee=?, t_m_milestone=? WHERE t_id=?",
            (params.get("title"), params.get("description"), params.get("asignee"), params.get("milestone"),
             params.get("id")))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/update_todo_status', methods=['POST'])
    @flask_login.login_required
    def update_todo_status():
        # Update status, create new event and return details of that new event.
        new_status = flask.request.json.get("status")
        todo_id = flask.request.json.get("todo_id")
        print(new_status)
        if type(todo_id) is not str:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Invalid todo_id.\"}",
                                  mimetype="application/json")
        if new_status not in (0, 1):
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Invalid status.\"}",
                                  mimetype="application/json")
        current_status = get_db().execute("SELECT t_status FROM todo WHERE t_id=?", (todo_id,)).fetchone()
        if current_status[0] is new_status:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Already same status.\"}",
                                  mimetype="application/json")
        get_db().execute("UPDATE todo SET t_status=? WHERE t_id=?", (new_status, todo_id))
        id = get_db().execute("INSERT INTO event (e_type, e_u_id, e_t_id) VALUES (?, ?, ?)",
                              (new_status, flask_login.current_user.id, todo_id)).lastrowid
        get_db().commit()
        res = get_db().execute("SELECT e_type, e_u_id, e_content, e_timestamp FROM event WHERE e_id=?",
                               (id,)).fetchone()
        return flask.Response("{\"status\": \"ok\", \"new_event\": " + json.dumps(
            {"type": res[0], "user": res[1], "content": res[2], "timestamp": res[3]}) + "}",
                              mimetype="application/json")
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
        # Remove todo and associated events

        # timestamps = get_db().execute("SELECT t_ts_created, t_ts_closed FROM todo WHERE t_id=?",
        #                               (flask.request.json.get("id"),)).fetchall()
        # if not timestamps:
        #     return flask.Response("{\"status\": \"error\", \"error_message\": \"Unknown id.\"}",
        #                           mimetype="application/json")
        # get_db().execute("DELETE FROM timestamp WHERE ts_id IN (?, ?)", timestamps[0])
        # rowcount = get_db().execute("DELETE FROM todo WHERE t_id=?", (flask.request.json.get("id"),)).rowcount
        # get_db().commit()
        # if rowcount != 1:
        #     return flask.Response("{\"status\": \"error\", \"error_message\": \"Unknown id.\"}",
        #                           mimetype="application/json")
        # return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        return "Not implemented. (need to reimplement)"
        # TODO: IMPLEMENT!!!

    @app.route('/api/remove_label', methods=['POST'])
    @flask_login.login_required
    def remove_label():
        # TODO: Validation
        # Remove label and associated todo_and_label entries
        get_db().execute("DELETE FROM label WHERE l_id=?", (flask.request.json.get("label_id"),))
        get_db().execute("DELETE FROM todo_and_label WHERE tl_l_label=?", (flask.request.json.get("label_id"),))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/remove_milestone', methods=['POST'])
    @flask_login.login_required
    def remove_milestone():
        # TODO: Validation
        # Remove milestone and remove references from todos
        get_db().execute("DELETE FROM milestone WHERE m_id=?", (flask.request.json.get("milestone_id"),))
        get_db().execute("UPDATE todo SET t_m_milestone=? WHERE t_m_milestone=?",
                         (None, flask.request.json.get("milestone_id")))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        # TODO: Test

    @app.route('/api/remove_project', methods=['POST'])
    @flask_login.login_required
    def remove_project():
        # TODO Validation
        # Remove project, associated todos, todo_and_label & milestones
        project_id = flask.request.json.get("project_id")
        get_db().execute("DELETE FROM project WHERE p_id=?", (project_id,))
        todostoremove = get_db().execute("SELECT t_id FROM todo WHERE t_p_project=?", (project_id,)).fetchall()
        remove = ()  # build a clean tuple list
        for a in todostoremove:
            remove += (a[0],)
        get_db().execute("DELETE FROM todo WHERE t_p_project=?", (project_id,))
        get_db().execute('DELETE FROM todo_and_label WHERE tl_t_todo IN (%s)' %
                         ','.join('?' * len(remove)), remove)  # see http://stackoverflow.com/a/1310001/3527128
        get_db().execute("DELETE FROM milestone WHERE m_p_project=?", (project_id,))
        get_db().commit()
        return flask.Response("{\"status\": \"ok\"}", mimetype="application/json")
        # TODO: Test

    # -------------------------- GET --------------------------

    @app.route('/api/get_todo_detail', methods=['GET'])
    @flask_login.login_required
    def get_details():
        # TODO: get asignee name (subselect)
        # TODO: Validation
        response = get_db().execute(
            "SELECT t.t_id, t.t_title, t.t_description, t.t_u_asignee, t.t_m_milestone, t.t_status FROM todo t WHERE t.t_id=?",
            (flask.request.args.get("id"),)).fetchone()
        if response is None:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        ret = {"id": response[0], "title": response[1], "description": response[2], "asignee": response[3],
               "milestone": response[4], "status": response[5]}
        return flask.Response(json.dumps(ret), mimetype="application/json")

    @app.route('/api/get_todos', methods=['GET'])
    @flask_login.login_required
    def get_todo_details():
        # TODO: Validation
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
        for a in result:
            ret.append({"id": a[0], "title": a[1], "description": a[2], "status": a[3]})
        return json.dumps(ret)
        # TODO: Test

    @app.route('/api/get_milestones', methods=['GET'])
    @flask_login.login_required
    def get_milestones():
        # TODO: Validation
        result = get_db().execute("SELECT m_id, m_title, m_status FROM milestone WHERE m_p_project=?",
                                  (flask.request.args.get("project_id"),)).fetchall()
        print(result)
        ret = []
        for a in result:
            ret.append(
                {"id": a[0], "title": a[1], "status": a[2]})
        return json.dumps(ret)

    @app.route('/api/get_milestones_by_name', methods=['GET'])
    @flask_login.login_required
    def get_milestones_by_name():
        if not flask.request.args.get("name"):
            search = "%"
        else:
            search = "%" + flask.request.args.get("name") + "%"
        result = get_db().execute(
            "SELECT m_id, m_title, m_status FROM milestone WHERE m_p_project=? AND m_title LIKE ? COLLATE nocase",
            (flask.request.args.get("project_id"), search)).fetchall()
        print(result)
        ret = []
        for a in result:
            ret.append(
                {"id": a[0], "title": a[1], "status": a[2]})
        return json.dumps(ret)

    @app.route('/api/get_milestone', methods=['GET'])
    @flask_login.login_required
    def get_milestone():
        # TODO: Validation
        result = get_db().execute(
            "SELECT m_title, m_description, m_duedate, m_status FROM milestone WHERE m_id=?",
            (flask.request.args.get("milestone_id"),)).fetchone()
        if not result:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        return json.dumps({"title": result[0], "description": result[1], "duedate": result[2],
                           "status": result[3]})

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
        # TODO: Validation
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
        res = get_db().execute("SELECT u_id, u_name FROM user WHERE u_name LIKE ? COLLATE nocase LIMIT 10",
                               (search,)).fetchall()
        ret = []
        for tupl in res:
            ret.append({"id": tupl[0], "name": tupl[1]})
        return json.dumps(ret)

    @app.route('/api/get_events', methods=['GET'])
    @flask_login.login_required
    def get_events():
        # TODO: Validation
        results = get_db().execute(
            "SELECT e_type, e_u_id, e_content, e_timestamp FROM event WHERE e_t_id=? ORDER BY e_timestamp",
            (flask.request.args.get("id"),)).fetchall()
        if results is None:
            return flask.Response("{\"status\": \"error\", \"error_message\": \"Not found.\"}",
                                  mimetype="application/json")
        ret = []
        index = 0
        for a in results:
            ret.append({"type": a[0], "user": a[1], "content": a[2], "timestamp": a[3], "index": index})
            index += 1
        return json.dumps(ret)
        # TODO: Test

    @app.route('/api/get_labels', methods=['GET'])
    @flask_login.login_required
    def get_labels():
        res = get_db().execute("SELECT l_id, l_name, l_color FROM label").fetchall()
        ret = []
        for a in res:
            ret.append({"id": a[0], "name": a[1], "color": a[2]})
        return json.dumps(ret)
        # TODO: Test

    @app.route('/api/get_assigned_labels', methods=['GET'])
    @flask_login.login_required
    def get_assigned_labels():
        # TODO: Validation
        if not flask.request.args.get("id"):
            return flask.Response("{\"status\": \"error\", \"error_message\": \"No id given.\"}",
                                  mimetype="application/json")
        result = get_db().execute("SELECT tl_l_label FROM todo_and_label WHERE tl_t_todo=?",
                                  (flask.request.args.get("id"),)).fetchall()
        ret = []
        for a in result:
            ret.append(a[0])
        return json.dumps(ret)

    # -------------------------- OTHER --------------------------

    @app.route('/<path:filename>')
    def catch_all(filename):
        return flask.send_from_directory('static', filename)

    @login_manager.user_loader  # should create user object (get from database etc), called when user object is needed
    def user_loader(user_id):
        print("=== user_loader ===")
        userdb = get_db().execute("SELECT u_id, u_name FROM user WHERE u_id=?", (user_id,))
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
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("Finishing because of 'test' argument.")
        return
    if config.use_ssl:
        ssl_context = ('server.crt', 'server.key')
    else:
        ssl_context = None

    try:
        app.run(host=config.host,
                port=config.port,
                ssl_context=ssl_context,
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
