#!/usr/bin/env bash
# Mirrors CI: KUBERNETES_KUBECONFORM_OPTIONS in .github/workflows/lint.yaml.
# Keep the -skip list in sync with the workflow.
set -euo pipefail

if ! command -v kubeconform >/dev/null; then
  echo "kubeconform not found — run ./hack/setup.sh" >&2
  exit 1
fi

# -ignore-missing-schemas: CRD kinds (CNPG, MetalLB, cert-manager, traefik…)
# have no upstream schema; CI only lints changed files so it rarely sees them.
# Same posture as the repo's KUBERNETES_KUBEVAL_OPTIONS.
exec kubeconform \
  -skip HelmRelease,Kustomization,Component,PrometheusRule,ExternalSecret,Secret \
  -ignore-missing-schemas \
  "$@"
