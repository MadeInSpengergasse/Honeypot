CREATE TABLE IF NOT EXISTS users (
  u_name         VARCHAR(100),
  u_id           INTEGER NOT NULL PRIMARY KEY,
  u_access_token VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS labels (
  l_id    INTEGER NOT NULL PRIMARY KEY,
  l_name  VARCHAR(50),
  l_color VARCHAR(7)
);

CREATE TABLE IF NOT EXISTS project (
  p_id          INTEGER PRIMARY KEY NOT NULL,
  p_title       VARCHAR(100),
  p_description VARCHAR(300),
  p_status      VARCHAR(1)          NOT NULL
);


CREATE TABLE IF NOT EXISTS timestamp (
  ts_id        INTEGER PRIMARY KEY NOT NULL,
  ts_u_id      INTEGER             NOT NULL,
  ts_timestamp DATETIME DEFAULT current_timestamp,
  FOREIGN KEY (ts_u_id) REFERENCES users (u_id)
);

CREATE TABLE IF NOT EXISTS milestone (
  m_id          INTEGER PRIMARY KEY NOT NULL,
  m_title       VARCHAR(100),
  m_description VARCHAR(300),
  m_starttime   DATETIME,
  m_endtime     DATETIME,
  m_p_project   INTEGER,
  m_status      VARCHAR(1)          NOT NULL,
  FOREIGN KEY (m_p_project) REFERENCES project (p_id)
);

CREATE TABLE IF NOT EXISTS todo (
  t_id          INTEGER      NOT NULL PRIMARY KEY AUTOINCREMENT,
  t_title       VARCHAR(100) NOT NULL,
  t_description VARCHAR(300) NOT NULL,
  t_u_asignee   INTEGER,
  t_m_milestone INTEGER,
  t_status      VARCHAR(1)   NOT NULL,
  t_ts_created  INTEGER      NOT NULL,
  t_ts_closed   INTEGER,
  t_p_project   INTEGER,
  FOREIGN KEY (t_p_project)
  REFERENCES project (p_id),

  FOREIGN KEY (t_u_asignee) REFERENCES users (u_id),
  FOREIGN KEY (t_m_milestone) REFERENCES milestone (m_id),
  FOREIGN KEY (t_ts_created) REFERENCES timestamp (ts_timestamp),
  FOREIGN KEY (t_ts_closed) REFERENCES timestamp (ts_timestamp)
);

CREATE TABLE IF NOT EXISTS todo_and_label (
  tl_id      INTEGER PRIMARY KEY  NOT NULL,
  tl_t_todo  INTEGER              NOT NULL,
  tl_l_label INTEGER              NOT NULL,

  FOREIGN KEY (tl_t_todo) REFERENCES todo (t_id),
  FOREIGN KEY (tl_l_label) REFERENCES labels (l_id)
);
