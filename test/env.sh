#!/bin/bash

SCRIPT_DIR="$(dirname $(readlink -f ${BASH_SOURCE[0]}))"
BLUETOOL_DIR="$(cd $SCRIPT_DIR/..; pwd)"
export PYTHONPATH="${PYTHONPATH}${PYTHONPATH:+:}${BLUETOOL_DIR}"
