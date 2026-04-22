#!/bin/bash
PROJECT_DIR="/home/viniciusgati/code/itagrest"
cd $PROJECT_DIR
source .venv_stable/bin/activate
export APP_ENV=homolog
export PYTHONNOUSERSITE=1
unset PYTHONPATH
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
