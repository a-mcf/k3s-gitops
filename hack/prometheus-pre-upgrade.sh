# https://github.com/prometheus-community/helm-charts/issues/108#issuecomment-825689328
# change version (up or down) then:
kubectl delete mutatingwebhookconfiguration/kube-prometheus-stack-admission -A
kubectl delete validatingwebhookconfiguration/kube-prometheus-stack-admission -A

echo "REMEMBER TO UPDATE ASSOCIATED CRDS!"
