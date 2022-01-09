# change version (up or down) then:
kubectl delete mutatingwebhookconfiguration/kube-prometheus-stack-admission -A
kubectl delete validatingwebhookconfiguration/kube-prometheus-stack-admission -A