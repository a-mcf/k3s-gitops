Manually sync Flux with your Git repository
```sh
flux reconcile source git flux-system
```

Show the health of you kustomizations
```sh
kubectl get kustomization -A
```

Show the health of your main Flux `GitRepository`
```sh
flux get sources git
```

Show the health of your `HelmRelease`s
```sh
flux get helmrelease -A
```

Show the health of your `HelmRepository`s
```sh
flux get sources helm -A
```

Delete pods in an error state:
```sh
kubectl delete pods --field-selector status.phase=Failed
```

Get details on a helm release:
```sh
kubectl describe -n <namespace> helmrelease/<release>
```

Get a shell on a running container:
```
kubectl exec --stdin --tty shell-demo -- /bin/bash
```

Get helm history:
```
helm history <release_name>
```
Unstick a helm release reporting >another operation (install/upgrade/rollback) is in progress>
```
kubectl get secret -A | grep <app-name> # find the helm secret with the latest version
kubectl delete secret <secret> -n <namespace> 
```

Force retries of failed helm releases by suspending / resuming:
https://github.com/fluxcd/helm-controller/issues/454
```
flux suspend hr <name>
flux resume hr <name>
```
