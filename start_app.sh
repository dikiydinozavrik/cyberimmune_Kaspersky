#!/bin/sh

export FLASK_DEBUG=1; python /decision_server/decision_server.py &
cd / ; python /update_server/update_server.py /update_server/config.ini
