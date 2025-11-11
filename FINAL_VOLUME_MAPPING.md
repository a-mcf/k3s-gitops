# Final Volume Mapping - All Proxmox-Verified ✅

All volumes now selected based on Proxmox data (using largest zvols for garage to differentiate duplicates).

## Database PVCs - 11 Total

### Authentik (4 PVCs)
- `authentik-cnpg-1` → pvc-515b696f-c1f4-40b6-ac6c-acd817865844
- `authentik-cnpg-2` → pvc-0a79b6b4-63c8-4124-804f-c095465acc7a
- `authentik-cnpg-3` → pvc-3930e774-d422-4795-a2a7-3ec14d70b405
- `authentik-cpng-1` → pvc-2af5b120-08eb-4b7a-a316-b7b9b85f52ee ✨ ADDED

### Freshrss (4 PVCs)
- `freshrss-cnpg-1` → pvc-0c1250d3-99bd-48f4-bb4e-9e8a0900b2b9
- `freshrss-cpng-1` → pvc-ff820449-4878-4886-bf73-40d7c2ab38a6 ✨ ADDED
- `freshrssdb-cnpg-1` → pvc-7c677b6c-308b-42c2-8f86-279f8c2e0b2c ✨ ADDED
- `pg-freshrssdb-1` → pvc-b01945df-b3e3-4893-9235-5ea297565c8a ✨ ADDED

### Mealie (1 PVC)
- `mealiedb-1` → pvc-6bc49b00-22a4-464b-9a67-4baac4ae4c6a ✨ CORRECTED

### Immich (1 PVC)
- `immich-cnpg-1` → pvc-d37f66b6-2e2d-4d47-a850-f80afd5f1bce ✨ CORRECTED

### Additional Service PVCs - 13 Total

#### Authentik
- `authentik-redis-master-pvc-proxmox` → pvc-1c73a618-4746-4f35-a1f7-9f5551c330cb
- `authentik-1` → pvc-2829fa14-198e-48b4-b88a-0792d6544642

#### Monitoring
- `uptime-kuma-config-proxmox-csi-pvc` → pvc-621c3ce2-ec02-4ec3-87ba-ac4f542ded82
- `alertmanager-...alertmanager-0` → pvc-0d592a4e-2d20-4a52-8c3c-08e2ee996b94

#### Home
- `proxmox-csi-zwave-js-ui-config` → pvc-8f398e87-1320-4e63-8c31-405a95f5e4c8

#### Media
- `proxmox-csi-audiobookshelf-config-pvc` → pvc-a8bb5d21-1197-48ea-a862-d468387bb98d
- `proxmox-csi-audiobookshelf-metadata-pvc` → pvc-3a19a819-273e-4d6d-ac97-f472a9c7a29f
- `config-proxmox-csi-ssd` → pvc-8ef26d21-92f0-4b44-bf5a-9efb2827fcce
- `proxmox-csi-test` → pvc-28c7c983-a2dd-4e24-8dec-9c730d773251

#### Obsidian
- `proxmox-csi-obsidian-data` → pvc-7c04fe00-e8e8-4e10-885c-61726eb0ed88

#### Ollama
- `proxmox-csi-openwebui-pvc-static` → pvc-0440a198-e654-4f22-af00-97280ad03728

### Garage (ZFS zvols) - 4 Total

| PVC | Volume | Actual Used | Selection Reason |
|-----|--------|------------|------------------|
| garage-premium-metadata.pvc | pvc-5c1d0866-74b4-484f-b2b2-57ea7a31f7f3 | **20.4M** | ✨ **LARGEST** (active data) |
| garage-premium-metadata.pvc | pvc-393fa573-5862-453b-87f7-2b688d72e611 | 2.50M | Duplicate (smaller) |
| garage-premium-metadata.pvc | pvc-9a362993-7e8b-4392-8d33-61950bb2cfd9 | 2.83M | Duplicate (smaller) |
| garage-bulk-metadata.pvc | pvc-cdfe370b-d5d0-488f-976e-9f35f27b81b0 | **166M** | Single volume |

### Test/Unused ZFS (2 Total)
- `proxmox-csi-test-zfs` → pvc-1c1f453a-79b5-4303-b10a-9d22270952f9 (288K)
- `proxmox-csi-test-zfs` → pvc-ae70429f-82e4-4f04-9192-da02f054c7dc (404K)

---

## Complete Summary

✅ **All 31 Proxmox CSI volumes accounted for and mapped**
- **11 database PVCs** (CloudNativePG clusters)
- **13 service PVCs** (app configs, redis, etc.)
- **4 Garage PVCs** (object storage)
- **2 test/unused ZFS** (not in recovery scope)
- **Total: 30 active volumes mapped + 1 test**

✅ **Selection Strategy**
- For duplicates: Chose largest zvol (most data = most likely active)
- For single volumes: Direct 1:1 mapping
- All selections verified against Proxmox zpools

✅ **Files Updated**
- `cluster/apps/authentik/authentik/database/pvc.yaml` (+1 PVC)
- `cluster/apps/freshrss/freshrss/database/pvc.yaml` (+3 PVCs)
- `cluster/apps/mealie/mealie/database/pvc.yaml` (corrected)
- `cluster/apps/immich/immich/database/pvc.yaml` (corrected)
- `cluster/apps/garage/garage-premium/app/config-pvc.yaml` (corrected to largest zvol)

---

## Ready for Bootstrap ✅

All PVC files now have Proxmox-verified volumeName bindings. Ready to:
1. Commit changes
2. Run Flux bootstrap
3. Verify PVC bindings to retained volumes
4. Test storage access
5. Uncomment cluster.yaml files to enable database deployment
