#!/bin/bash
source env/bin/activate
export FLASK_APP=webapp.py
export FLASK_ENV=development
flask run
