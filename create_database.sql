CREATE TABLE IF NOT EXISTS users (
  u_id           INTEGER NOT NULL PRIMARY KEY,
  u_name         TEXT,
  u_access_token TEXT
);

CREATE TABLE IF NOT EXISTS labels (
  l_id    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  l_name  TEXT,
  l_color TEXT
);

CREATE TABLE IF NOT EXISTS project (
  p_id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  p_title       TEXT,
  p_description TEXT,
  p_status      TEXT    NOT NULL
);


CREATE TABLE IF NOT EXISTS timestamp (
  ts_id        INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  ts_u_id      INTEGER NOT NULL,
  ts_timestamp DATETIME                     DEFAULT current_timestamp,

  FOREIGN KEY (ts_u_id) REFERENCES users (u_id)
);

CREATE TABLE IF NOT EXISTS milestone (
  m_id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  m_title       TEXT,
  m_description TEXT,
  m_starttime   DATETIME,
  m_endtime     DATETIME,
  m_p_project   INTEGER,
  m_status      INTEGER NOT NULL,

  FOREIGN KEY (m_p_project) REFERENCES project (p_id)
);

CREATE TABLE IF NOT EXISTS todo (
  t_id          INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  t_title       TEXT    NOT NULL,
  t_description TEXT    NOT NULL,
  t_u_asignee   INTEGER,
  t_m_milestone INTEGER,
  t_status      INTEGER NOT NULL,
  t_ts_created  INTEGER NOT NULL,
  t_ts_closed   INTEGER,
  t_p_project   INTEGER,

  FOREIGN KEY (t_p_project) REFERENCES project (p_id),
  FOREIGN KEY (t_u_asignee) REFERENCES users (u_id),
  FOREIGN KEY (t_m_milestone) REFERENCES milestone (m_id),
  FOREIGN KEY (t_ts_created) REFERENCES timestamp (ts_timestamp),
  FOREIGN KEY (t_ts_closed) REFERENCES timestamp (ts_timestamp)
);

CREATE TABLE IF NOT EXISTS todo_and_label (
  tl_id      INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
  tl_t_todo  INTEGER NOT NULL,
  tl_l_label INTEGER NOT NULL,

  FOREIGN KEY (tl_t_todo) REFERENCES todo (t_id),
  FOREIGN KEY (tl_l_label) REFERENCES labels (l_id)
);
