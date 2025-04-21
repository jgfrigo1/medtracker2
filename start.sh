#!/bin/bash
flask db upgrade || echo "No migration needed"
gunicorn -w 4 -b 0.0.0.0:10000 "medtracker:create_app()"
