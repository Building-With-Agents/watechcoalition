# WaTech VM Rebuild Status

## Completed Phases ✅

### Phase 1: Pre-Execution Safety Checks ✅
- Verified all protected resources exist:
  - Public IP: 20.106.201.34 ✅
  - NIC: careerserviceprod862_z1 ✅
  - NSG: CareerServiceProd-nsg (SSH, HTTP, HTTPS rules) ✅
  - VNet: career-services-test-vnet ✅
  - Image Gallery: CareerServicesImageGallery ✅
- Documented current VM state (Standard_D2as_v4, 8GB RAM)
- Identified OS disk for deletion

### Phase 2: SSH Keypair Generation ✅
- Generated new SSH ed25519 keypair:
  - Private key: `C:\Users\garyl\.ssh\watech_cfa_vm`
  - Public key: `C:\Users\garyl\.ssh\watech_cfa_vm.pub`
  - Passphrase: `sty7qxmw!`
- **Manual step required**: Convert to PPK format using PuTTYgen

### Phase 3: Delete Compromised Resources ✅
- Deallocated CareerServiceProd VM
- Deleted CareerServiceProd VM
- Deleted old OS disk (CareerServiceProd_OsDisk_1_26ffe91ee430410c8ddf27e9dc36d9e8)
- Verified all protected resources still intact

### Phase 4: Create Clean VM ✅
- Created WatechProd-v2 with:
  - Ubuntu 22.04 image
  - Standard_B2s size (4GB RAM, 2 vCPUs)
  - Admin username: azwatechadmin
  - New SSH key configured
- Disabled accelerated networking on preserved NIC (not supported by Standard_B2s)
- Attached preserved NIC (careerserviceprod862_z1) with:
  - Public IP: CareerServiceProd-ip (20.106.201.34)
  - NSG: CareerServiceProd-nsg
- Deleted auto-generated NIC (WatechProd-v2VMNic)
- Started VM successfully

## Next Steps (Requires SSH Access) 📋

### Phase 5-7: VM Configuration
All steps are documented in `docs/VM_CONFIGURATION_STEPS.md`

**Connection Details:**
- IP: 20.106.201.34
- User: azwatechadmin
- SSH Key: C:\Users\garyl\.ssh\watech_cfa_vm.ppk (after conversion)
- Passphrase: sty7qxmw!

**Tasks to Complete:**
1. Convert SSH key to PPK format (PuTTYgen)
2. Connect via PuTTY
3. Configure 2GB swap file
4. Install and configure fail2ban
5. Harden SSH configuration
6. Install Node.js 22 via NVM
7. Install PM2
8. Clone application repository
9. Update Next.js to latest
10. Build application
11. Configure PM2 to run application
12. Create future reinstatement documentation
13. Configure .env file (only active variables)
14. Security validation scans
15. Verify application health

## Protected Resources Status ✅

All protected resources are intact and properly configured:

| Resource | Name | Status | Notes |
|----------|------|--------|-------|
| VM | WatechProd-v2 | ✅ Running | Standard_B2s, Ubuntu 22.04 |
| Public IP | CareerServiceProd-ip | ✅ Active | 20.106.201.34 |
| NIC | careerserviceprod862_z1 | ✅ Attached | Connected to WatechProd-v2 |
| NSG | CareerServiceProd-nsg | ✅ Active | SSH, HTTP, HTTPS rules |
| VNet | career-services-test-vnet | ✅ Active | |
| Image Gallery | CareerServicesImageGallery | ✅ Active | |

## Deleted Resources ✅

| Resource | Name | Status |
|----------|------|--------|
| VM | CareerServiceProd | ✅ Deleted |
| OS Disk | CareerServiceProd_OsDisk_1_26ffe91ee430410c8ddf27e9dc36d9e8 | ✅ Deleted |
| NIC | WatechProd-v2VMNic | ✅ Deleted |

## Environment Configuration

### Current .env Variables (Active)
```
NEXT_PUBLIC_DOMAIN=www.watechcoalition.org
NEXT_PUBLIC_TENANT_ID=a3c7a257-40f2-43a9-9373-8bb5fc6862f7
NEXT_PUBLIC_CLIENT_ID=dfc4e746-44b7-420b-8463-ad6011728b8d
NEXT_PUBLIC_BASE_URL=https://cfahelpdesksandbox.api.crm.dynamics.com/api/data/v9.1
NEXT_PUBLIC_TOKEN_SCOPE=https://cfahelpdesksandbox.crm.dynamics.com/.default
CP_APPLICATION_ENDPOINT=<to-be-provided>
AI_DEV_ENDPOINT=<to-be-provided>
```

### Future Reinstatement Variables (Documented)
All authentication, database, Azure Storage, and Azure OpenAI variables are documented in `docs/FUTURE_REINSTATEMENT.md` for future implementation. These are currently unused.

## Security Notes

- ✅ New VM created from clean Ubuntu 22.04 image
- ✅ New SSH keypair generated (not reused)
- ✅ Old compromised VM and disk deleted
- ⏳ SSH hardening pending (after initial connection)
- ⏳ fail2ban installation pending
- ⏳ Security validation scans pending

## Repository Information

- **Repository**: https://CFA1@dev.azure.com/CFA1/Career%20Services/_git/CoalitionWebsite
- **Clone Directory**: frontend-cfa
- **Build Command**: npm run build
- **Start Command**: npm run start (via PM2)

## Important Notes

1. **Login/Authentication**: Not currently implemented. All auth-related variables moved to future reinstatement docs.
2. **NodeMailer**: Deprecated, email config removed.
3. **MSSQL Tools**: Not included in this deployment.
4. **VM Size**: Changed from Standard_D2as_v4 (8GB) to Standard_B2s (4GB) as per plan.
5. **Next.js**: Will be updated to latest version during application deployment.

## Final Checklist (To Be Completed)

- [ ] Convert SSH key to PPK format
- [ ] Establish SSH connection
- [ ] Configure 2GB swap file
- [ ] Install and configure fail2ban
- [ ] Harden SSH (disable password auth, disable root login)
- [ ] Install Node.js 22.x via NVM
- [ ] Install PM2
- [ ] Clone application repository
- [ ] Update Next.js to latest
- [ ] Build application
- [ ] Configure PM2 startup
- [ ] Create future reinstatement documentation on VM
- [ ] Configure .env file
- [ ] Run security validation scans
- [ ] Verify no malicious processes
- [ ] Verify no suspicious cron jobs
- [ ] Verify application responding
- [ ] Delete any remaining auto-generated Azure resources

