#!/usr/bin/env sh
waitress-serve --host 127.0.0.1 --port 8000 --call project:create_app