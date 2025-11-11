# PersistentVolume to PersistentVolumeClaim Mapping

All Proxmox CSI volumes that need to be recovered:

| PV Name | Namespace | PVC Name | Storage Class | Volume Handle |
|---------|-----------|----------|---------------|----------------|
| pvc-0440a198-e654-4f22-af00-97280ad03728 | ollama | proxmox-csi-openwebui-pvc-static | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-0440a198-e654-4f22-af00-97280ad03728.raw |
| pvc-0a79b6b4-63c8-4124-804f-c095465acc7a | authentik | authentik-cnpg-2 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-0a79b6b4-63c8-4124-804f-c095465acc7a.raw |
| pvc-0c1250d3-99bd-48f4-bb4e-9e8a0900b2b9 | freshrss | freshrss-cnpg-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-0c1250d3-99bd-48f4-bb4e-9e8a0900b2b9.raw |
| pvc-0d592a4e-2d20-4a52-8c3c-08e2ee996b94 | monitoring | alertmanager-kube-prometheus-stack-alertmanager-db-alertmanager-kube-prometheus-stack-alertmanager-0 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-0d592a4e-2d20-4a52-8c3c-08e2ee996b94.raw |
| pvc-0e4c9ffa-d893-4dc2-b982-9610b6983596 | immich | immich-cnpg-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-0e4c9ffa-d893-4dc2-b982-9610b6983596.raw |
| pvc-1c1f453a-79b5-4303-b10a-9d22270952f9 | media | proxmox-csi-test-zfs | proxmox-csi-ext4-ssd-zfs | bitworld/shodan/local-zfs/vm-9999-pvc-1c1f453a-79b5-4303-b10a-9d22270952f9 |
| pvc-1c73a618-4746-4f35-a1f7-9f5551c330cb | authentik | authentik-redis-master-pvc-proxmox | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-1c73a618-4746-4f35-a1f7-9f5551c330cb.raw |
| pvc-2829fa14-198e-48b4-b88a-0792d6544642 | authentik | authentik-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-2829fa14-198e-48b4-b88a-0792d6544642.raw |
| pvc-28c7c983-a2dd-4e24-8dec-9c730d773251 | media | proxmox-csi-test | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-28c7c983-a2dd-4e24-8dec-9c730d773251.raw |
| pvc-2af5b120-08eb-4b7a-a316-b7b9b85f52ee | authentik | authentik-cpng-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-2af5b120-08eb-4b7a-a316-b7b9b85f52ee.raw |
| pvc-3930e774-d422-4795-a2a7-3ec14d70b405 | authentik | authentik-cnpg-3 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-3930e774-d422-4795-a2a7-3ec14d70b405.raw |
| pvc-393fa573-5862-453b-87f7-2b688d72e611 | garage | garage-premium-metadata.pvc | proxmox-csi-ext4-ssd-zfs | bitworld/shodan/local-zfs/vm-9999-pvc-393fa573-5862-453b-87f7-2b688d72e611 |
| pvc-3a19a819-273e-4d6d-ac97-f472a9c7a29f | media | proxmox-csi-audiobookshelf-metadata-pvc | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-3a19a819-273e-4d6d-ac97-f472a9c7a29f.raw |
| pvc-3fe15344-e089-44f6-b41c-b0cf1a02f885 | freshrss | mealiedb-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-3fe15344-e089-44f6-b41c-b0cf1a02f885.raw |
| pvc-430040db-fcbc-4717-9ebc-d053b7d7e434 | freshrss | freshrss-cpgn-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-430040db-fcbc-4717-9ebc-d053b7d7e434.raw |
| pvc-4e25fb83-f17f-4d03-86fd-57db5ebe54f2 | mealie | mealiedb-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-4e25fb83-f17f-4d03-86fd-57db5ebe54f2.raw |
| pvc-515b696f-c1f4-40b6-ac6c-acd817865844 | authentik | authentik-cnpg-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-515b696f-c1f4-40b6-ac6c-acd817865844.raw |
| pvc-5c1d0866-74b4-484f-b2b2-57ea7a31f7f3 | garage | garage-premium-metadata.pvc | proxmox-csi-ext4-ssd-zfs | bitworld/shodan/local-zfs/vm-9999-pvc-5c1d0866-74b4-484f-b2b2-57ea7a31f7f3 |
| pvc-621c3ce2-ec02-4ec3-87ba-ac4f542ded82 | monitoring | uptime-kuma-config-proxmox-csi-pvc | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-621c3ce2-ec02-4ec3-87ba-ac4f542ded82.raw |
| pvc-6bc49b00-22a4-464b-9a67-4baac4ae4c6a | mealie | mealiedb-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-6bc49b00-22a4-464b-9a67-4baac4ae4c6a.raw |
| pvc-78c912f7-9545-4e12-835f-e793d28dd983 | authentik | authentik-cpng-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-78c912f7-9545-4e12-835f-e793d28dd983.raw |
| pvc-7c04fe00-e8e8-4e10-885c-61726eb0ed88 | obsidian-couchdb | proxmox-csi-obsidian-data | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-7c04fe00-e8e8-4e10-885c-61726eb0ed88.raw |
| pvc-7c677b6c-308b-42c2-8f86-279f8c2e0b2c | freshrss | freshrssdb-cnpg-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-7c677b6c-308b-42c2-8f86-279f8c2e0b2c.raw |
| pvc-86d1e433-3559-49b0-b790-e6570f581d7a | freshrss | freshrss-cpng-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-86d1e433-3559-49b0-b790-e6570f581d7a.raw |
| pvc-8ef26d21-92f0-4b44-bf5a-9efb2827fcce | media | config-proxmox-csi-ssd | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-8ef26d21-92f0-4b44-bf5a-9efb2827fcce.raw |
| pvc-8f398e87-1320-4e63-8c31-405a95f5e4c8 | home | proxmox-csi-zwave-js-ui-config | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-8f398e87-1320-4e63-8c31-405a95f5e4c8.raw |
| pvc-92fd41bd-31b4-46ff-8f33-1f1cdfbee76f | authentik | authentik-cpng-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-92fd41bd-31b4-46ff-8f33-1f1cdfbee76f.raw |
| pvc-9a362993-7e8b-4392-8d33-61950bb2cfd9 | garage | garage-premium-metadata.pvc | proxmox-csi-ext4-ssd-zfs | bitworld/shodan/local-zfs/vm-9999-pvc-9a362993-7e8b-4392-8d33-61950bb2cfd9 |
| pvc-a8bb5d21-1197-48ea-a862-d468387bb98d | media | proxmox-csi-audiobookshelf-config-pvc | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-a8bb5d21-1197-48ea-a862-d468387bb98d.raw |
| pvc-ae70429f-82e4-4f04-9192-da02f054c7dc | media | proxmox-csi-test-zfs | proxmox-csi-ext4-ssd-zfs | bitworld/shodan/local-zfs/vm-9999-pvc-ae70429f-82e4-4f04-9192-da02f054c7dc |
| pvc-b01945df-b3e3-4893-9235-5ea297565c8a | freshrss | pg-freshrssdb-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-b01945df-b3e3-4893-9235-5ea297565c8a.raw |
| pvc-b049fabd-4f77-4abd-bde5-65d628460691 | mealie | mealiedb-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-b049fabd-4f77-4abd-bde5-65d628460691.raw |
| pvc-cdfe370b-d5d0-488f-976e-9f35f27b81b0 | garage | garage-bulk-metadata.pvc | proxmox-csi-ext4-ssd-zfs | bitworld/shodan/local-zfs/vm-9999-pvc-cdfe370b-d5d0-488f-976e-9f35f27b81b0 |
| pvc-d37f66b6-2e2d-4d47-a850-f80afd5f1bce | immich | immich-cnpg-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-d37f66b6-2e2d-4d47-a850-f80afd5f1bce.raw |
| pvc-dff7302d-b15c-45c2-b17a-1929dbdfc0b0 | freshrss | freshrss-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-dff7302d-b15c-45c2-b17a-1929dbdfc0b0.raw |
| pvc-f2ab393a-f73c-4e79-ae6f-0a461604f2eb | authentik | authentik-cpng-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-f2ab393a-f73c-4e79-ae6f-0a461604f2eb.raw |
| pvc-f8fa6c72-d07b-4f55-836f-37cb96bb2299 | freshrss | pg-freshrssdb-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-f8fa6c72-d07b-4f55-836f-37cb96bb2299.raw |
| pvc-ff820449-4878-4886-bf73-40d7c2ab38a6 | freshrss | freshrss-cpng-1 | proxmox-csi-ext4-ssd | bitworld/shodan/vmdata/9999/vm-9999-pvc-ff820449-4878-4886-bf73-40d7c2ab38a6.raw |

## Key Database Volumes
- authentik-cnpg-1, authentik-cnpg-2, authentik-cnpg-3 (3-instance cluster)
- freshrss-cnpg-1 (1 instance)
- mealie: multiple (1 instance but multiple PVCs)
- immich-cnpg-1 (1 instance)

## Garage Volumes
- garage-premium-metadata.pvc (3 volumes)
- garage-bulk-metadata.pvc (1 volume)

## Application Config Volumes
- authentik-redis-master-pvc-proxmox
- proxmox-csi-audiobookshelf-metadata-pvc and config
- proxmox-csi-obsidian-data
- uptime-kuma-config-proxmox-csi-pvc
- proxmox-csi-zwave-js-ui-config
