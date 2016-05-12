# Generate it with
# import os
# os.urandom(24)
secret_key = b''
# GitHub OAuth tokens
github_client_id = ""
github_client_secret = ""

# --- WEBSERVER ---
# Port to run the webserver
port = 5000
# Host (use 0.0.0.0 to listen on all interfaces, just modify it if you know what you are doing!)
host = '0.0.0.0'
# If flask should be started in debug mode
debug = True
# Should the webserver be secured with ssl? If yes, there has to be a server.crt & server.key file.
use_ssl = False
