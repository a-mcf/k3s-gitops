# Proxmox-Verified Volume Mappings - Updated

Successfully updated all database PVC files with Proxmox-verified volumes!

## Changes Made

### ✅ Authentik (4 PVCs - 3-instance + 1 extra)
**File**: `cluster/apps/authentik/authentik/database/pvc.yaml`
- authentik-cnpg-1: pvc-515b696f-c1f4-40b6-ac6c-acd817865844 ✓ (was correct)
- authentik-cnpg-2: pvc-0a79b6b4-63c8-4124-804f-c095465acc7a ✓ (was correct)
- authentik-cnpg-3: pvc-3930e774-d422-4795-a2a7-3ec14d70b405 ✓ (was correct)
- **authentik-cpng-1: pvc-2af5b120-08eb-4b7a-a316-b7b9b85f52ee ← ADDED (was missing)**

### ✅ Freshrss (4 PVCs - multiple databases)
**File**: `cluster/apps/freshrss/freshrss/database/pvc.yaml`
- freshrss-cnpg-1: pvc-0c1250d3-99bd-48f4-bb4e-9e8a0900b2b9 ✓ (unchanged)
- **freshrss-cpng-1: pvc-ff820449-4878-4886-bf73-40d7c2ab38a6 ← ADDED (was missing)**
- **freshrssdb-cnpg-1: pvc-7c677b6c-308b-42c2-8f86-279f8c2e0b2c ← ADDED (was missing)**
- **pg-freshrssdb-1: pvc-b01945df-b3e3-4893-9235-5ea297565c8a ← ADDED (was missing)**

### ✅ Mealie (1 PVC)
**File**: `cluster/apps/mealie/mealie/database/pvc.yaml`
- **mealiedb-1: pvc-6bc49b00-22a4-464b-9a67-4baac4ae4c6a ← CORRECTED**
  - (was: pvc-4e25fb83-f17f-4d03-86fd-57db5ebe54f2)

### ✅ Immich (1 PVC)
**File**: `cluster/apps/immich/immich/database/pvc.yaml`
- **immich-cnpg-1: pvc-d37f66b6-2e2d-4d47-a850-f80afd5f1bce ← CORRECTED**
  - (was: pvc-0e4c9ffa-d893-4dc2-b982-9610b6983596)

## Summary
- ✅ All database PVCs now match Proxmox-verified list
- ✅ 4 additional PVCs created for authentik and freshrss
- ✅ 2 PVCs corrected (mealie, immich)
- **Total database PVCs: 11** (was 6)

---

## ⚠️ Garage Decision Needed

Your Proxmox list shows **3 garage-premium-metadata.pvc zvols**:
```
garage/garage-premium-metadata.pvc → pvc-9a362993-7e8b-4392-8d33-61950bb2cfd9
garage/garage-premium-metadata.pvc → pvc-393fa573-5862-453b-87f7-2b688d72e611
garage/garage-premium-metadata.pvc → pvc-5c1d0866-74b4-484f-b2b2-57ea7a31f7f3
```

I currently have in config-pvc.yaml:
```yaml
volumeName: pvc-393fa573-5862-453b-87f7-2b688d72e611
```

**Question**: Which one should we use?
- The one with most recent timestamp?
- The largest one?
- Do you know which one is actively in use?

Once you confirm, I'll update the garage config-pvc.yaml files.

---

## Next Steps

1. **Confirm garage-premium selection** (which of the 3 zvols?)
2. Update garage-premium if needed
3. Commit all changes
4. Bootstrap Flux
