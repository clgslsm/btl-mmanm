#!/bin/sh

nginx -g "daemon on;" && cd /opt/backend && flask run --host 0.0.0.0 --port 5000