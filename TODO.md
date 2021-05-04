Research:
Figure out why this was required to get new deploys to validate:
 ```
 kubectl get validatingwebhookconfigurations
 kubectl delete validatingwebhookconfigurations ingress-nginx-admission
 ```

 Known Issues:
 - When doing a new nextcloud install the nfs export needs 777 starting out.