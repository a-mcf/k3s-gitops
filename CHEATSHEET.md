Manually sync Flux with your Git repository
```sh
flux --kubeconfig=./kubeconfig reconcile source git flux-system
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