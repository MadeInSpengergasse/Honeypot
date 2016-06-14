#Database:
###Users
u_name (name for user, just for display)
u_id (github unique id for user)
u_access_token (github user access token)
u_access_level (0=admin, 1=guest)

###Labels
l_id (unique id)
l_name (name of the label eg "bug")
l_color (how to color it)

__m <-> n relationship between labels and todos!__

###ToDo's
t_id (unique id) (not null)
t_title (big title) (not null, no empty string)
t_description (longer text) (not null, only empty string)
t_u_assignee (user id; more than one?) (can be null)
t_m_milestone (milestone id) (can be null)
t_status (closed?) (0=open, 1=closed)
t_ts_created (timestamp of created) (not null)
t_ts_closed (timestamp of closed) (can be null)

###Milestone
m_id (unique id)
m_title (big title)
m_description (long-ish description)
m_duedate (when it should be finished)
m_p_project
m_status (closed?)

###Project
p_id (unique id)
p_title (big title)
p_description (long-ish description)
p_status (closed?)

### Event
e_id INTEGER (unique id)
e_u_id INTEGER (user who did that)
e_t_id INTEGER (todo id)
e_type INTEGER (0=opened, 1=closed, 2=comment, 3=add_label, 4=remove_label, 5=add_assignee, 6=remove_assignee)
e_content TEXT (comment content or other values we need (such as user_id))
e_timestamp TEXT (timestamp)