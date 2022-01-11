# pass in nextcloud pod name as first variable
kubectl exec -n nextcloud --stdin --tty $1 -- su -p www-data -s /bin/bash -c '/var/www/html/occ maintenance:mode --off'