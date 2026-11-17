#!/usr/bin/env bash
# Copy the release fixture into the run's empty working directory.
set -euo pipefail
cp -r "$(dirname "${BASH_SOURCE[0]}")/../fixtures/release/." .
