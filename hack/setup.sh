#!/usr/bin/env bash
# One-shot dev setup: install the tools the pre-commit hooks need, then
# register the hooks. Safe to re-run.
set -euo pipefail

KUBECONFORM_VERSION=v0.6.7 # matches the super-linter CI image
KUBECONFORM_SHA256=95f14e87aa28c09d5941f11bd024c1d02fdc0303ccaa23f61cef67bc92619d73
BIN_DIR="${HOME}/.local/bin"

cd "$(git rev-parse --show-toplevel)"
mkdir -p "${BIN_DIR}"

if ! command -v pre-commit >/dev/null; then
	echo "==> installing pre-commit via pipx"
	pipx install pre-commit
fi

if ! command -v kubeconform >/dev/null; then
	echo "==> installing kubeconform ${KUBECONFORM_VERSION} to ${BIN_DIR}"
	tmp=$(mktemp -d)
	curl -sL -o "${tmp}/kubeconform.tar.gz" \
		"https://github.com/yannh/kubeconform/releases/download/${KUBECONFORM_VERSION}/kubeconform-linux-amd64.tar.gz"
	echo "${KUBECONFORM_SHA256}  ${tmp}/kubeconform.tar.gz" | sha256sum -c -
	tar -C "${BIN_DIR}" -xzf "${tmp}/kubeconform.tar.gz" kubeconform
	rm -rf "${tmp}"
fi

echo "==> registering git hooks"
pre-commit install

echo
echo "Done. Try it:  pre-commit run --all-files"
echo "Checkov (slow, optional):  pre-commit run checkov --hook-stage manual --all-files"
