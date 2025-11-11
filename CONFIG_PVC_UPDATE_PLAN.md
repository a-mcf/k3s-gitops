# Config PVC Update Plan - 25 Files

## Analysis Summary

From your 25 config-pvc.yaml files, here's the breakdown:

### ✅ FILES REQUIRING PROXMOX CSI volumeName UPDATES (14 files)

These files have Proxmox CSI storage and need volumeName bindings added:

| File Path | Namespace | PVC Name | volumeName UUID | Priority |
|-----------|-----------|----------|-----------------|----------|
| /cluster/apps/authentik/authentik/app/config-pvc.yaml | authentik | authentik-redis-master-pvc-proxmox | pvc-1c73a618-4746-4f35-a1f7-9f5551c330cb | ✅ DONE |
| /cluster/apps/garage/garage-bulk/app/config-pvc.yaml | garage | garage-bulk-metadata.pvc | pvc-cdfe370b-d5d0-488f-976e-9f35f27b81b0 | ✅ DONE |
| /cluster/apps/garage/garage-premium/app/config-pvc.yaml | garage | garage-premium-metadata.pvc | pvc-393fa573-5862-453b-87f7-2b688d72e611 | ✅ DONE |
| /cluster/apps/home/zwave-js-ui/app/config-pvc.yaml | home | proxmox-csi-zwave-js-ui-config | pvc-8f398e87-1320-4e63-8c31-405a95f5e4c8 | 🟡 TODO |
| /cluster/apps/media/audiobookshelf/app/config-pvc.yaml | media | proxmox-csi-audiobookshelf-metadata-pvc + proxmox-csi-audiobookshelf-config-pvc | pvc-3a19a819-273e-4d6d-ac97-f472a9c7a29f + pvc-a8bb5d21-1197-48ea-a862-d468387bb98d | 🟡 TODO |
| /cluster/apps/media/plex/app/config-pvc.yaml | media | config-proxmox-csi-ssd | pvc-8ef26d21-92f0-4b44-bf5a-9efb2827fcce | 🟡 TODO |
| /cluster/apps/monitoring/kube-prometheus-stack/app/config-pvc.yaml | monitoring | alertmanager-...alertmanager-0 | pvc-0d592a4e-2d20-4a52-8c3c-08e2ee996b94 | 🟡 TODO |
| /cluster/apps/monitoring/uptime-kuma/app/config-pvc.yaml | monitoring | uptime-kuma-config-proxmox-csi-pvc | pvc-621c3ce2-ec02-4ec3-87ba-ac4f542ded82 | 🟡 TODO |
| /cluster/apps/obsidian-couchdb/obsidian-couchdb/app/config-pvc.yaml | obsidian-couchdb | proxmox-csi-obsidian-data | pvc-7c04fe00-e8e8-4e10-885c-61726eb0ed88 | 🟡 TODO |
| /cluster/apps/ollama/ollama/webui/config-pvc.yaml | ollama | proxmox-csi-openwebui-pvc-static | pvc-0440a198-e654-4f22-af00-97280ad03728 | 🟡 TODO |

### ⏹️  NFS-ONLY FILES (NO UPDATES NEEDED - 11 files)

These files use only NFS storage and should be skipped:

| File Path | Storage Type | Notes |
|-----------|--------------|-------|
| /cluster/apps/freshrss/freshrss/app/config-pvc.yaml | NFS | Applications is NFS-backed only |
| /cluster/apps/home/esphome/app/config-pvc.yaml | NFS | nfs-esphome-config-pv |
| /cluster/apps/home/hass/app/config-pvc.yaml | NFS | Likely NFS (check if needed) |
| /cluster/apps/home/scrypted/app/config-pvc.yaml | NFS | Likely NFS (check if needed) |
| /cluster/apps/home/wyoming-piper/app/config-pvc.yaml | NFS | Likely NFS (check if needed) |
| /cluster/apps/home/wyoming-whisper/app/config-pvc.yaml | NFS | Likely NFS (check if needed) |
| /cluster/apps/minio/minio/app/config-pvc.yaml | NFS | Deprecated minio, using NFS nfs-minio-pv |
| /cluster/apps/monitoring/loki/app/config-pvc.yaml | NFS | nfs-loki-pv (storage-loki-0) |
| /cluster/apps/ollama/ollama/app/config-pvc.yaml | NFS | nfs-ollama-data-pv (note: webui is Proxmox) |
| /cluster/apps/opencloud/opencloud/app/config-pvc.yaml | Unknown | Not in PV mapping - verify/skip |
| /cluster/apps/paperless/paperless-ngx/app/config-pvc.yaml | Unknown | Not in PV mapping - verify/skip |
| /cluster/apps/photoprism/photoprism/app/config-pvc.yaml | Unknown | Not in PV mapping - verify/skip |
| /cluster/apps/syncthing/syncthing/app/config-pvc.yaml | Unknown | Not in PV mapping - verify/skip |

### 🟠 DATABASE PVCs - SPECIAL HANDLING

Database PVCs are managed by CloudNativePG Cluster resources and don't need explicit config-pvc.yaml entries. However, they DO need volumeName bindings to recover data from retained volumes.

**Files to Update (if separate PVC files exist):**
- immich-cnpg-1: pvc-0e4c9ffa-d893-4dc2-b982-9610b6983596
- mealie-cnpg: Multiple PVCs (pvc-4e25fb83, pvc-6bc49b00, pvc-b049fabd)
- freshrss database: Multiple PVCs (pvc-0c1250d3, pvc-430040db, etc.)
- authentik database: authentik-cnpg-1,2,3 + authentik-1

**CRITICAL:** These database volumes need binding in the cluster.yaml files under the Cluster spec, NOT in config-pvc.yaml files. The database PVs will be bound automatically when the StatefulSet starts if the volumeNames match the PVC names created by CloudNativePG.

## Update Strategy

### Phase 1: Update 10 App Config PVC Files (Proxmox CSI apps)
1. zwave-js-ui (1 PVC)
2. audiobookshelf (2 PVCs in same file)
3. plex (1 PVC)
4. uptime-kuma (1 PVC)
5. kube-prometheus-stack/alertmanager (1 PVC with long name)
6. obsidian-couchdb (1 PVC)
7. ollama webui (1 PVC)

### Phase 2: Verify NFS Files
Check that esphome, hass, scrypted, wyoming apps, loki, and others correctly reference NFS.

### Phase 3: Database PVC Recovery
Ensure database volumes are properly bound - may require additional config in cluster.yaml files or creation of new PVC definitions.

## Implementation Pattern

Standard volumeName addition for each PVC in config-pvc.yaml:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <pvc-name>
  namespace: <namespace>
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: <storage-size>
  storageClassName: proxmox-csi-ext4-ssd  # or proxmox-csi-ext4-ssd-zfs
  volumeMode: Filesystem
  volumeName: pvc-<uuid>  # ADD THIS LINE
```

The key is adding `volumeName: pvc-<uuid>` which will bind the PVC to the retained PV automatically.

## Files Already Updated ✅

- authentik redis: pvc-1c73a618-4746-4f35-a1f7-9f5551c330cb
- garage-premium: pvc-393fa573-5862-453b-87f7-2b688d72e611
- garage-bulk: pvc-cdfe370b-d5d0-488f-976e-9f35f27b81b0

## Remaining Work

- Update 10 app config-pvc.yaml files with volumeName
- Verify NFS storage paths in freshrss, esphome, home apps
- Test Flux bootstrap to verify PVC bindings work correctly
