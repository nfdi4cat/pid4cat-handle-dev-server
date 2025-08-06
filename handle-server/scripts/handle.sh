#!/bin/sh

HANDLE_BIN="/opt/handle/bin"
HANDLE_SVR="/var/handle/svr"

# Create the configuration for the server (substitute env.vars into Jinja2 templates)
# Changed from build.py (string.Template) to create_config.py (Jinja2) for better templating
python3 /home/handle/create_config.py $HANDLE_BIN $HANDLE_SVR

# Start the handle server
exec "$HANDLE_BIN/hdl-server" $HANDLE_SVR 2>&1
