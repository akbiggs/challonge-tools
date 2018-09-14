#!/bin/bash
source env/bin/activate
export FLASK_APP=webapp
export FLASK_ENV=development
export FLASK_SKIP_DOTENV=1
# flask run --host=0.0.0.0
flask run
