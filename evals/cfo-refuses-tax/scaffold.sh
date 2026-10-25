#!/bin/sh
# Copies the Studio North fixture workspace into the case workspace.
exec sh "$(dirname "$0")/../fixtures/workspace.sh" "${1:-$PWD}"
