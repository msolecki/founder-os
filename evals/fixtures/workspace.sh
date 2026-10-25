#!/bin/sh
# Copies the Studio North fixture workspace to <dir>/founder-os/, the default
# FOUNDER_OS_HOME the state gateway resolves from the project root.
# Usage: workspace.sh [dir]
set -eu
d=${1:-$PWD}
here=$(cd "$(dirname "$0")" && pwd -P)
mkdir -p "$d/founder-os"
cp -R "$here/studio-north/." "$d/founder-os/"
