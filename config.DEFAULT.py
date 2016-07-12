# Create the secret key with:
#     import os
#     os.urandom(24)
# KEEP IT SECRET!
secret_key = b''
# GitHub OAuth tokens
github_client_id = ""
github_client_secret = ""

# --- WEBSERVER ---
# If flask should be started in debug mode
debug = True
# Use WSGI? If yes, the options under this are all invalid and you have to have WSGI configured
use_wsgi = True
# Port to run the webserver
port = 5000
# Host (use 0.0.0.0 to listen on all interfaces, just modify it if you know what you are doing!)
host = '0.0.0.0'
# Should the webserver be secured with ssl? If yes, there has to be a server.crt & server.key file.
use_ssl = False
