flux-update:
	flux reconcile source git flux-system
	kubectl get kustomization -A
	flux get helmrelease -A
