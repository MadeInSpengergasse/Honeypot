#Database:
###Users
u_name (name for user, just for display)
u_id (github unique id for user)
u_access_token (github user access token)

###Labels
l_id (unique id)
l_name (name of the label eg "bug")
l_color (how to color it)

__m <-> n relationship between labels and todos!__

###ToDo's
t_id (unique id)
t_title (big title)
t_description (longer text)
t_u_asignee (user id; more than one?)
t_m_milestone (milestone id)
t_status (closed?)
t_ts_created (timestamp of created)
t_ts_closed (timestamp of closed)

###Milestone
m_id (unique id)
m_title (big title)
m_description (long-ish description)
m_starttime (when it should be active)
m_endtime (when it should be finished)
m_p_project
m_status (closed?)

###Project
p_id (unique id)
p_title (big title)
p_description (long-ish description)
p_status (closed?)

### Timestamp
ts_u_id (user who did that)
ts_timestamp (when it happened)
