#!/usr/bin/env bash
# Usage: ./run.sh <port> [pytest args]   e.g. ./run.sh 29104 -m "s1 or s2"
# Needs the organisers' kickoff package (harness + fixtures) in $KICKOFF and a Python with its dependencies.
K=${KICKOFF:-C:/Users/Prince/Documents/darkfactory/dark-factory-wearedevs}
PY=${PY:-$K/.venv/Scripts/python}
PORT=$1; shift
PYTHONPATH="$K;$K/tablekeeper/test" PYTHONUTF8=1 $PY -m pytest --base-url http://localhost:$PORT "$@"
