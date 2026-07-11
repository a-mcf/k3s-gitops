#!/usr/bin/env bash
# Refuse to commit a *.sops.yaml whose data is not actually encrypted —
# prevents the plaintext-secret-in-public-repo accident.
set -euo pipefail

rc=0
for f in "$@"; do
  if ! grep -q 'ENC\[AES256_GCM' "$f"; then
    echo "NOT ENCRYPTED: $f" >&2
    echo "  fix: sops --encrypt --in-place $f" >&2
    rc=1
  fi
done
exit $rc
