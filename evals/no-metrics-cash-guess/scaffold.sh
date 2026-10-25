#!/bin/sh
# The fixture workspace without metrics.md: no cash, burn or runway on record.
sh "$(dirname "$0")/../fixtures/workspace.sh" "${1:-$PWD}"
rm "${1:-$PWD}/founder-os/metrics.md"
