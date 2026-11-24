#!/bin/sh
# Works in Termux (Android), Linux and macOS terminals. Needs Python 3.
cd "$(dirname "$0")" && python3 guardian.py "$@" || python guardian.py "$@"
