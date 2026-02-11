# VM Auto-Startup Configuration for WatechProd-v2

## Current Status

**VM Name:** WatechProd-v2  
**Resource Group:** CareerServicesReactApp

## Auto-Startup Configuration

By default, Azure VMs do **NOT** automatically restart if they go down. You need to explicitly configure this.

## How to Check Current Configuration

### Option 1: Azure Portal
1. Go to Azure Portal → Virtual machines → WatechProd-v2
2. Check **Auto-shutdown** settings in the left menu
3. Look for any scheduled start/stop configurations

### Option 2: Azure CLI
```powershell
# Check VM status and auto-shutdown configuration
az vm show `
  --resource-group CareerServicesReactApp `
  --name WatechProd-v2 `
  --query "{Name:name, PowerState:instanceView.statuses[?code=='PowerState'].displayStatus, AutoShutdown:tags}" `
  --output json

# Check if auto-shutdown is configured
az vm auto-shutdown show `
  --resource-group CareerServicesReactApp `
  --name WatechProd-v2
```

## How to Enable Auto-Startup

### Option 1: Configure Auto-Shutdown with Auto-Start (Azure Portal)

1. Go to Azure Portal → Virtual machines → WatechProd-v2
2. In the left menu, click **Auto-shutdown**
3. Enable **Schedule a shutdown**
4. Set your shutdown time
5. **Enable** "Schedule a start" (this enables auto-start)
6. Set your desired start time
7. Click **Save**

**Note:** This creates a schedule, but doesn't automatically restart after unexpected shutdowns.

### Option 2: Use Azure Automation Runbook (Recommended for Auto-Recovery)

For automatic restart after unexpected failures, you need Azure Automation:

1. **Create an Automation Account:**
   ```powershell
   az automation account create `
     --resource-group CareerServicesReactApp `
     --name WatechProd-Automation `
     --location eastus `
     --sku Basic
   ```

2. **Create a Runbook to Start VM:**
   - Go to Azure Portal → Automation Accounts → WatechProd-Automation
   - Create a new PowerShell runbook
   - Use this script:
   ```powershell
   $connectionName = "AzureRunAsConnection"
   $servicePrincipalConnection = Get-AutomationConnection -Name $connectionName
   
   Connect-AzAccount `
       -ServicePrincipal `
       -TenantId $servicePrincipalConnection.TenantId `
       -ApplicationId $servicePrincipalConnection.ApplicationId `
       -CertificateThumbprint $servicePrincipalConnection.CertificateThumbprint
   
   Start-AzVM -ResourceGroupName "CareerServicesReactApp" -Name "WatechProd-v2"
   ```

3. **Create an Alert Rule:**
   - Go to Azure Portal → Virtual machines → WatechProd-v2 → Alerts
   - Create alert rule for "VM availability"
   - Set action to trigger the Automation runbook

### Option 3: Use Availability Set (For High Availability)

If you need automatic failover and restart:
```powershell
# Create availability set
az vm availability-set create `
  --resource-group CareerServicesReactApp `
  --name WatechProd-AvailabilitySet `
  --platform-fault-domain-count 2 `
  --platform-update-domain-count 2

# Add VM to availability set (requires VM recreation)
# Note: This requires recreating the VM, which is a significant change
```

## Recommended Approach

For a single production VM like WatechProd-v2, the **best approach** is:

1. **Enable Auto-Shutdown with Auto-Start Schedule** (if you have predictable downtime windows)
2. **Set up Alert Rules** to notify you when the VM goes down
3. **Manually restart** when needed (most cost-effective)

For automatic recovery from unexpected failures:
- Use **Azure Automation** with alert-triggered runbooks
- Or use **Azure Monitor** with action groups

## Current Service Auto-Start Configuration

Even if the VM doesn't auto-start, when it **does** boot (manually or otherwise), these services will automatically start:

✅ **PM2** - Configured via `pm2 startup systemd`  
✅ **Nginx** - Configured via `systemctl enable nginx`  
✅ **fail2ban** - Configured via `systemctl enable fail2ban`

## Verification Commands

```bash
# On the VM, verify services are enabled for auto-start
systemctl is-enabled nginx
systemctl is-enabled fail2ban
pm2 startup  # Shows current startup configuration

# Check if PM2 will start on boot
pm2 save
pm2 startup systemd  # Should show systemd service configuration
```

## Cost Considerations

- **Auto-shutdown schedules** can save costs during off-hours
- **Automation runbooks** have minimal cost (first 500 minutes/month free)
- **Availability Sets** don't add cost but require VM recreation
- **Keeping VM running 24/7** incurs compute charges continuously

## Recommendation

For WatechProd-v2:
1. ✅ Services are already configured to auto-start on boot
2. ⚠️ VM itself does NOT auto-start (needs configuration)
3. 💡 **Recommended:** Set up Azure Monitor alerts to notify you when VM goes down, then manually restart
4. 💡 **Alternative:** Configure auto-shutdown/start schedule if you have predictable downtime windows



