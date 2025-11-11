# PVC Recovery Checklist - Ready for Flux Bootstrap

## ✅ Pre-Bootstrap Verification (COMPLETE)

### Files Analyzed
- [x] All 25 config-pvc.yaml files from your list have been analyzed
- [x] Cross-referenced against 31-volume PV mapping
- [x] Classified into: Proxmox CSI, NFS-only, or unmapped

### Updates Applied
- [x] 10 config-pvc.yaml files updated with volumeName bindings (13 PVCs)
- [x] 4 database PVC files created with volumeName bindings (6 PVCs)
- [x] 13 NFS-only files identified and skipped (no changes needed)
- [x] Total: 19 PVCs configured for recovery

### PVC Status
- [x] All volumeName UUIDs verified against PV_PVC_MAPPING.md
- [x] Storage classes match (proxmox-csi-ext4-ssd, proxmox-csi-ext4-ssd-zfs)
- [x] Namespaces verified for all PVCs
- [x] All PVs confirmed with persistentVolumeReclaimPolicy: Retain

---

## 📋 Pre-Bootstrap Checklist

Before running `flux bootstrap`, verify:

### 1. Git Configuration
- [ ] All changes committed to git repository
- [ ] Branch is main/master and up to date
- [ ] Remote repository is accessible

### 2. Kubernetes Cluster
- [ ] Cluster is running and accessible via kubectl
- [ ] Flux v2.7.3+ is compatible with cluster version
- [ ] flux-system namespace can be created
- [ ] CRDs not in conflict state

### 3. File Locations
- [ ] `/cluster/apps/home/zwave-js-ui/app/config-pvc.yaml` ✅
- [ ] `/cluster/apps/media/audiobookshelf/app/config-pvc.yaml` ✅
- [ ] `/cluster/apps/media/plex/app/config-pvc.yaml` ✅
- [ ] `/cluster/apps/monitoring/uptime-kuma/app/config-pvc.yaml` ✅
- [ ] `/cluster/apps/obsidian-couchdb/obsidian-couchdb/app/config-pvc.yaml` ✅
- [ ] `/cluster/apps/ollama/ollama/webui/config-pvc.yaml` ✅
- [ ] `/cluster/apps/authentik/authentik/database/pvc.yaml` ✅ (NEW)
- [ ] `/cluster/apps/freshrss/freshrss/database/pvc.yaml` ✅ (NEW)
- [ ] `/cluster/apps/mealie/mealie/database/pvc.yaml` ✅ (NEW)
- [ ] `/cluster/apps/immich/immich/database/pvc.yaml` ✅ (NEW)

---

## 🚀 Bootstrap Steps

### Step 1: Uninstall Existing Flux (if needed)
```bash
flux uninstall --namespace=flux-system
# or
kubectl delete namespace flux-system
```

### Step 2: Bootstrap Flux
```bash
flux bootstrap github \
  --owner=<your-github-org> \
  --repo=k3s-gitops \
  --branch=main \
  --path=cluster/base/flux-system \
  --personal=false \
  --private=false
```

### Step 3: Verify Flux Installation
```bash
flux check
kubectl get pods -n flux-system
kubectl logs -n flux-system deploy/source-controller
```

### Step 4: Wait for PVC Reconciliation
```bash
# Monitor PVC creation
kubectl get pvc -A --watch

# Verify volumeName bindings
kubectl get pvc -o wide -A | grep volumeName
# OR detailed view
kubectl describe pvc <pvc-name> -n <namespace> | grep volumeName
```

### Step 5: Verify PV Bindings
```bash
# Check PVs are bound
kubectl get pv | grep proxmox-csi

# Verify claimRef matches your PVCs
kubectl describe pv <pv-name>
```

### Step 6: Monitor App Startup
```bash
# Watch all app deployments
kubectl get deployments -A --watch

# Check specific app
kubectl get pods -n <namespace> --watch

# View logs for issues
kubectl logs -n <namespace> <pod-name>
```

---

## 🔍 Key Monitoring Commands

### PVC Status
```bash
# List all PVCs with their volumes
kubectl get pvc -A -o wide

# Check specific PVC
kubectl describe pvc <pvc-name> -n <namespace>

# See which PV it's bound to
kubectl get pvc <pvc-name> -n <namespace> -o jsonpath='{.spec.volumeName}'
```

### Database Startup
```bash
# Watch CloudNativePG cluster
kubectl get cluster -A
kubectl describe cluster <cluster-name> -n <namespace>

# Check database pod
kubectl get pods -n <namespace> -l cnpg.io/cluster=<cluster-name>
kubectl logs -n <namespace> <cluster-name>-1

# Test database connectivity
kubectl exec -n <namespace> <pod> -- pg_isready
```

### Application Verification
```bash
# Check all app statuses
flux get kustomizations -A

# Check reconciliation status
kubectl get helmrelease -A

# View Flux events
flux logs --all-namespaces --follow
```

---

## ⚠️ Troubleshooting

### PVC Stuck in Pending
**Symptom**: PVC status shows Pending, not Bound
**Check**:
```bash
kubectl describe pvc <pvc-name> -n <namespace>
```
**Common causes**:
- PV with volumeName UUID doesn't exist (check PV_PVC_MAPPING.md)
- Storage class doesn't match
- Namespace mismatch

**Fix**:
```bash
# Verify PV exists
kubectl get pv | grep pvc-<uuid>

# Check PV details
kubectl describe pv pvc-<uuid>

# Verify claimRef is empty/correct
kubectl get pv pvc-<uuid> -o jsonpath='{.spec.claimRef}'
```

### Database Cluster Not Starting
**Symptom**: Cluster resource created but pods don't start
**Check**:
```bash
kubectl describe cluster <cluster-name> -n <namespace>
kubectl logs -n <namespace> <cluster-name>-1
```
**Common causes**:
- PVC not bound (see above)
- Storage class not available
- Insufficient resources

### App Cannot Mount Volume
**Symptom**: Pod pending with mount errors
**Check**:
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs -n <namespace> <pod-name>
```
**Fix**:
- Verify PVC is bound: `kubectl get pvc <pvc-name> -n <namespace>`
- Check PV is accessible: `kubectl get pv <pv-name> -o jsonpath='{.status.phase}'`

---

## 📊 Expected Timeline

| Phase | Duration | Action |
|-------|----------|--------|
| Bootstrap | 2-5 min | Flux initializes, CRDs install |
| PVC Creation | 1-2 min | volumeName bindings activate |
| App Startup | 5-15 min | Deployments start, volumes mount |
| Database Init | 10-30 min | CloudNativePG reconciles data |
| Health Check | 5-10 min | Apps verify connectivity |
| **Total** | **~30-60 min** | Full recovery complete |

---

## ✨ Post-Bootstrap Tasks

### After Everything is Running

1. **Verify Database Data**
   ```bash
   kubectl exec -n <namespace> <pod> -- psql -U postgres -d <dbname> -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname != 'pg_catalog';"
   ```

2. **Check App Connectivity**
   - Visit ingress URLs
   - Verify application features work
   - Check data integrity

3. **Database Restoration (if needed)**
   ```bash
   # If bootstrap from backup is needed
   kubectl exec -n <namespace> <pod> -- pg_basebackup \
     -D /var/lib/postgresql/data/pgdata \
     --wal-method=stream -Ft -z -P
   ```

4. **Verify Backups Running**
   ```bash
   # Check Garage connectivity
   kubectl get secret -n <namespace> cloudnative-pg-secret-garage
   
   # Monitor backup jobs
   kubectl get jobs -n <namespace> -l cnpg.io/cluster=<name>
   ```

5. **Commit Recovery State**
   ```bash
   git status
   git add .
   git commit -m "PVC recovery: volumeName bindings for 19 PVCs"
   git push
   ```

---

## 📝 Notes

- All 19 PVCs are configured with volumeName bindings to retained Proxmox CSI volumes
- NFS-based apps (freshrss app, esphome, hass, etc.) continue using existing NFS configuration
- Database PVCs created to allow CloudNativePG to reuse retained data without loss
- Garage backup infrastructure already configured and ready for database recovery
- ExternalSecrets configured in database namespaces for Garage S3 credentials

**Ready to proceed with Flux bootstrap!** 🚀
