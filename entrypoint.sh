#!/bin/bash

# Docker container entry point script
# When you run docker run my-app xyz, then this script will get run

# Set the number of gevent workers to number of cores * 2 + 1
# See: http://docs.gunicorn.org/en/stable/design.html#how-many-workers
n_workers="$(($(nproc) * 2 + 1))"
# Use the WORKERS environment variable, if present
workers=${WORKERS:-$n_workers}

# Persistent server mode (aka "dynamic service"):
# This is run when there are no arguments
if [ $# -eq 0 ] ; then
  echo "Running in persistent server mode"
  gunicorn \
    --worker-class gevent \
    --timeout 1800 \
    --workers $workers \
    --bind :5000 \
    ${DEVELOPMENT:+"--reload"} \
    src.server:app

# Run tests
elif [ "${1}" = "test" ] ; then
  echo "Running tests..."
  flake8 --max-complexity 10 src
  mypy --ignore-missing-imports src
  python -m pyflakes src
  bandit -r src
  python -m unittest discover src/test
  echo "...done running tests."

# One-off jobs
elif [ "${1}" = "async" ] ; then
  echo "Running a one-off job... nothing to do."

# Initialize?
elif [ "${1}" = "init" ] ; then
  echo "Initializing module... nothing to do."

# Bash shell in the container
elif [ "${1}" = "bash" ] ; then
  echo "Launching a bash shell in the docker container."
  bash

# Required file for registering the module on the KBase catalog
elif [ "${1}" = "report" ] ; then
  echo "Generating report..."
  cp /kb/module/compile_report.json /kb/module/work/compile_report.json

else
  echo "Unknown command. Valid commands are: test, async, init, bash, or report"
fi
