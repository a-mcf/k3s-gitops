#!/usr/bin/env bash
# Whole-tree kustomize builds (~0.5s) — catches wiring mistakes plain file
# linting can't: unregistered apps, broken resource lists, the Component
# accumulation trap that broke the flux-system build in #1608.
set -euo pipefail

kubectl kustomize cluster/apps > /dev/null
kubectl kustomize cluster/base > /dev/null
echo "cluster/apps + cluster/base build clean"
