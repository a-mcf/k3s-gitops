flux-update:
	flux reconcile source git flux-system
	kubectl get kustomization -A
	flux get helmrelease -A
edit-secrets:
	sops ./cluster/base/cluster-secrets.yaml
