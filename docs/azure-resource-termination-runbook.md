# Azure Resource Termination Runbook

## Overview

This runbook provides step-by-step instructions to fully delete all checked resources in the CareerServicesReactApp resource group using Azure CLI. Resources will be deleted in dependency order to avoid blocking errors, with confirmation prompts for any dependencies not explicitly checked.

## Resources to Delete (Checked Items)

### SQL Resources

- `cfa-reactdb` (SQL server)
- `vector-search` (SQL database on cfa-reactdb)

### Function App Resources

- `jsearchjobfetch` (Function App)
- `jsearchjobfetch` (Application Insights)
- `Failure Anomalies - jsearchjobfetch` (Smart detector alert rule)

### AI/Cognitive Services

- `myOAIResource508483` (Azure OpenAI)
- `resumeJobMatch` (Document intelligence)

### VM and Network Resources (career-services-test)

- `career-services-test` (Virtual machine)
- `career-services-test` (SQL virtual machine)
- `career-services-test-ip` (Public IP address)
- `career-services-test-nsg` (Network security group)
- `career-services-test-vnet` (Virtual network)
- `career-services-test967` (Network Interface)
- `career-services-test_disk1_6fb85f0f70604bfcb5e8c7317204f1e5` (Disk)
- `career-services-test_key` (SSH key)

### Backup Resources

- `test-server-restore-points` (Restore Point Collection)

## Prerequisites

### Required Tools

- Azure CLI installed and configured
- Access to Azure subscription with appropriate permissions:
  - SQL DB Contributor role (for database deletion)
  - Virtual Machine Contributor role (for VM deletion)
  - Network Contributor role (for network resource deletion)
  - Cognitive Services Contributor role (for AI service deletion)
  - Application Insights Component Contributor role (for Application Insights deletion)

### Required Information

- Resource Group: `CareerServicesReactApp`
- All resource names as listed above

## Step 1: Authenticate and Set Context

```powershell
# Login to Azure
az login

# Set subscription (if multiple subscriptions)
az account set --subscription "<subscription-id>"

# Verify current subscription
az account show

# Set default resource group
az configure --defaults group=CareerServicesReactApp
```

## Step 2: List and Verify Resources

```powershell
# List all resources in the resource group
Write-Host "=== All Resources in CareerServicesReactApp ===" -ForegroundColor Cyan
az resource list `
  --resource-group CareerServicesReactApp `
  --query "[].{Name:name, Type:type, Location:location}" `
  --output table

# Verify checked resources exist
Write-Host "`n=== Verifying Checked Resources ===" -ForegroundColor Yellow
$CHECKED_RESOURCES = @(
    "cfa-reactdb",
    "vector-search",
    "jsearchjobfetch",
    "myOAIResource508483",
    "resumeJobMatch",
    "career-services-test",
    "career-services-test-ip",
    "career-services-test-nsg",
    "career-services-test-vnet",
    "career-services-test967",
    "career-services-test_disk1_6fb85f0f70604bfcb5e8c7317204f1e5",
    "career-services-test_key",
    "test-server-restore-points"
)

foreach ($resource in $CHECKED_RESOURCES) {
    $exists = az resource show `
      --resource-group CareerServicesReactApp `
      --name $resource `
      --query "name" `
      --output tsv 2>$null
    if ($exists) {
        Write-Host "✓ Found: $resource" -ForegroundColor Green
    } else {
        Write-Host "✗ Not found: $resource" -ForegroundColor Red
    }
}
```

## Step 3: Delete Smart Detector Alert Rules

```powershell
# Delete Failure Anomalies alert rule
# Note: Smart detector alert rules are deleted using resource delete with full resource ID
Write-Host "`n=== Step 3: Deleting Smart Detector Alert Rules ===" -ForegroundColor Cyan

# First, find the alert rule resource ID
$ALERT_RULE_ID = az resource list `
  --resource-group CareerServicesReactApp `
  --query "[?contains(name, 'Failure Anomalies') && contains(name, 'jsearchjobfetch')].id" `
  --output tsv

if ($ALERT_RULE_ID) {
    Write-Host "Deleting Failure Anomalies alert rule..." -ForegroundColor Yellow
    az resource delete --ids $ALERT_RULE_ID --yes
    Write-Host "✓ Alert rule deleted" -ForegroundColor Green
} else {
    Write-Host "Alert rule not found or already deleted" -ForegroundColor Yellow
}
```

## Step 4: Delete Function App Resources

```powershell
# Delete Function App and Application Insights
Write-Host "`n=== Step 4: Deleting Function App Resources ===" -ForegroundColor Cyan

# Stop Function App first (if running)
Write-Host "Stopping Function App 'jsearchjobfetch'..." -ForegroundColor Yellow
az functionapp stop `
  --resource-group CareerServicesReactApp `
  --name jsearchjobfetch 2>$null

# Delete Function App
Write-Host "Deleting Function App 'jsearchjobfetch'..." -ForegroundColor Yellow
az functionapp delete `
  --resource-group CareerServicesReactApp `
  --name jsearchjobfetch `
  --yes

Write-Host "✓ Function App deleted" -ForegroundColor Green

# Delete Application Insights
Write-Host "Deleting Application Insights 'jsearchjobfetch'..." -ForegroundColor Yellow
az monitor app-insights component delete `
  --resource-group CareerServicesReactApp `
  --app jsearchjobfetch `
  --yes

Write-Host "✓ Application Insights deleted" -ForegroundColor Green

# Check for any dependencies not on checked list
Write-Host "`nChecking for unlisted dependencies..." -ForegroundColor Yellow
$DEPENDENCIES = az resource list `
  --resource-group CareerServicesReactApp `
  --query "[?contains(name, 'jsearchjobfetch')].{Name:name, Type:type}" `
  --output table

if ($DEPENDENCIES) {
    Write-Host "WARNING: Found additional resources related to jsearchjobfetch:" -ForegroundColor Red
    Write-Host $DEPENDENCIES
    $confirm = Read-Host "Delete these resources? (y/N)"
    if ($confirm -eq 'y') {
        # Delete additional dependencies
        # Add deletion commands here based on resource types found
    }
}
```

## Step 5: Delete AI/Cognitive Services

```powershell
# Delete AI/Cognitive Services
Write-Host "`n=== Step 5: Deleting AI/Cognitive Services ===" -ForegroundColor Cyan

# Delete Document Intelligence (resumeJobMatch)
Write-Host "Deleting Document Intelligence 'resumeJobMatch'..." -ForegroundColor Yellow
az cognitiveservices account delete `
  --resource-group CareerServicesReactApp `
  --name resumeJobMatch `
  --yes

Write-Host "✓ Document Intelligence deleted" -ForegroundColor Green

# Delete Azure OpenAI (myOAIResource508483)
Write-Host "Deleting Azure OpenAI 'myOAIResource508483'..." -ForegroundColor Yellow
az cognitiveservices account delete `
  --resource-group CareerServicesReactApp `
  --name myOAIResource508483 `
  --yes

Write-Host "✓ Azure OpenAI deleted" -ForegroundColor Green

# Check for any dependencies not on checked list
Write-Host "`nChecking for unlisted dependencies..." -ForegroundColor Yellow
$DEPENDENCIES = az resource list `
  --resource-group CareerServicesReactApp `
  --query "[?name=='resumeJobMatch' || name=='myOAIResource508483'].{Name:name, Type:type}" `
  --output table

if ($DEPENDENCIES) {
    Write-Host "WARNING: Found additional resources:" -ForegroundColor Red
    Write-Host $DEPENDENCIES
    $confirm = Read-Host "Delete these resources? (y/N)"
    if ($confirm -eq 'y') {
        # Delete additional dependencies
    }
}
```

## Step 6: Delete SQL Resources

```powershell
# Delete SQL Resources
Write-Host "`n=== Step 6: Deleting SQL Resources ===" -ForegroundColor Cyan

# IMPORTANT: Delete databases before deleting the server
# Delete SQL database (vector-search)
Write-Host "Deleting SQL database 'vector-search'..." -ForegroundColor Yellow
az sql db delete `
  --resource-group CareerServicesReactApp `
  --server cfa-reactdb `
  --name vector-search `
  --yes

Write-Host "✓ SQL database 'vector-search' deleted" -ForegroundColor Green

# Verify no other databases exist on the server (except master)
Write-Host "`nChecking for remaining databases on server..." -ForegroundColor Yellow
$REMAINING_DBS = az sql db list `
  --resource-group CareerServicesReactApp `
  --server cfa-reactdb `
  --query "[?name!='master'].{Name:name}" `
  --output tsv

if ($REMAINING_DBS) {
    Write-Host "WARNING: Found additional databases on server:" -ForegroundColor Red
    Write-Host $REMAINING_DBS
    $confirm = Read-Host "Delete these databases? (y/N)"
    if ($confirm -eq 'y') {
        foreach ($db in $REMAINING_DBS) {
            Write-Host "Deleting database '$db'..." -ForegroundColor Yellow
            az sql db delete `
              --resource-group CareerServicesReactApp `
              --server cfa-reactdb `
              --name $db `
              --yes
        }
    } else {
        Write-Host "Skipping SQL server deletion due to remaining databases" -ForegroundColor Yellow
        exit
    }
}

# Delete SQL server (cfa-reactdb)
Write-Host "Deleting SQL server 'cfa-reactdb'..." -ForegroundColor Yellow
az sql server delete `
  --resource-group CareerServicesReactApp `
  --name cfa-reactdb `
  --yes

Write-Host "✓ SQL server 'cfa-reactdb' deleted" -ForegroundColor Green
```

## Step 7: Delete VM and Network Resources

```powershell
# Delete VM and Network Resources
Write-Host "`n=== Step 7: Deleting VM and Network Resources ===" -ForegroundColor Cyan

# Check VM status first
Write-Host "Checking VM status..." -ForegroundColor Yellow
$VM_STATUS = az vm show `
  --resource-group CareerServicesReactApp `
  --name career-services-test `
  --query "powerState" `
  --output tsv 2>$null

if ($VM_STATUS -and $VM_STATUS -ne "VM deallocated") {
    Write-Host "VM is running. Stopping and deallocating..." -ForegroundColor Yellow
    az vm deallocate `
      --resource-group CareerServicesReactApp `
      --name career-services-test
    Write-Host "Waiting for VM to deallocate..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

# Delete SQL VM extension (if exists)
Write-Host "Checking for SQL VM extension..." -ForegroundColor Yellow
$SQL_EXT = az vm extension list `
  --resource-group CareerServicesReactApp `
  --vm-name career-services-test `
  --query "[?contains(name, 'SqlIaaSAgent')].name" `
  --output tsv 2>$null

if ($SQL_EXT) {
    Write-Host "Deleting SQL VM extension..." -ForegroundColor Yellow
    az vm extension delete `
      --resource-group CareerServicesReactApp `
      --vm-name career-services-test `
      --name $SQL_EXT
}

# Delete Virtual Machine
Write-Host "Deleting Virtual Machine 'career-services-test'..." -ForegroundColor Yellow
az vm delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test `
  --yes

Write-Host "✓ Virtual Machine deleted" -ForegroundColor Green

# Delete Network Interface (must be deleted before IP/NSG/VNet)
Write-Host "Deleting Network Interface 'career-services-test967'..." -ForegroundColor Yellow
az network nic delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test967 `
  --yes

Write-Host "✓ Network Interface deleted" -ForegroundColor Green

# Delete Public IP Address
Write-Host "Deleting Public IP 'career-services-test-ip'..." -ForegroundColor Yellow
az network public-ip delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test-ip `
  --yes

Write-Host "✓ Public IP deleted" -ForegroundColor Green

# Delete Network Security Group
Write-Host "Deleting Network Security Group 'career-services-test-nsg'..." -ForegroundColor Yellow
az network nsg delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test-nsg `
  --yes

Write-Host "✓ Network Security Group deleted" -ForegroundColor Green

# Delete Virtual Network (must be deleted after all network resources)
Write-Host "Deleting Virtual Network 'career-services-test-vnet'..." -ForegroundColor Yellow
az network vnet delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test-vnet `
  --yes

Write-Host "✓ Virtual Network deleted" -ForegroundColor Green

# Delete Disk
Write-Host "Deleting Disk 'career-services-test_disk1_6fb85f0f70604bfcb5e8c7317204f1e5'..." -ForegroundColor Yellow
az disk delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test_disk1_6fb85f0f70604bfcb5e8c7317204f1e5 `
  --yes

Write-Host "✓ Disk deleted" -ForegroundColor Green

# Delete SSH Key
Write-Host "Deleting SSH Key 'career-services-test_key'..." -ForegroundColor Yellow
az sshkey delete `
  --resource-group CareerServicesReactApp `
  --name career-services-test_key `
  --yes

Write-Host "✓ SSH Key deleted" -ForegroundColor Green

# Check for any dependencies not on checked list
Write-Host "`nChecking for unlisted VM/network dependencies..." -ForegroundColor Yellow
$DEPENDENCIES = az resource list `
  --resource-group CareerServicesReactApp `
  --query "[?contains(name, 'career-services-test')].{Name:name, Type:type}" `
  --output table

if ($DEPENDENCIES) {
    Write-Host "WARNING: Found additional resources related to career-services-test:" -ForegroundColor Red
    Write-Host $DEPENDENCIES
    $confirm = Read-Host "Delete these resources? (y/N)"
    if ($confirm -eq 'y') {
        # Delete additional dependencies based on resource types
        # This would need to be customized based on what's found
    }
}
```

## Step 8: Delete Backup Resources

```powershell
# Delete Restore Point Collection
Write-Host "`n=== Step 8: Deleting Backup Resources ===" -ForegroundColor Cyan

Write-Host "Deleting Restore Point Collection 'test-server-restore-points'..." -ForegroundColor Yellow
az restore-point collection delete `
  --resource-group CareerServicesReactApp `
  --collection-name test-server-restore-points `
  --yes

Write-Host "✓ Restore Point Collection deleted" -ForegroundColor Green
```

## Step 9: Final Verification

```powershell
# Final verification
Write-Host "`n=== Step 9: Final Verification ===" -ForegroundColor Cyan

# List all remaining resources
Write-Host "Remaining resources in CareerServicesReactApp:" -ForegroundColor Yellow
az resource list `
  --resource-group CareerServicesReactApp `
  --query "[].{Name:name, Type:type, Location:location}" `
  --output table

# Verify all checked resources are deleted
Write-Host "`nVerifying all checked resources are deleted..." -ForegroundColor Yellow
$ALL_DELETED = $true
foreach ($resource in $CHECKED_RESOURCES) {
    $exists = az resource show `
      --resource-group CareerServicesReactApp `
      --name $resource `
      --query "name" `
      --output tsv 2>$null
    if ($exists) {
        Write-Host "✗ Still exists: $resource" -ForegroundColor Red
        $ALL_DELETED = $false
    } else {
        Write-Host "✓ Deleted: $resource" -ForegroundColor Green
    }
}

if ($ALL_DELETED) {
    Write-Host "`n✓ All checked resources have been successfully deleted!" -ForegroundColor Green
} else {
    Write-Host "`n⚠ Some resources could not be deleted. Please review the list above." -ForegroundColor Yellow
}
```

## Error Handling

### If Function App Deletion Fails

```powershell
# Check Function App status
az functionapp show `
  --resource-group CareerServicesReactApp `
  --name jsearchjobfetch `
  --query "{Name:name, State:state, HostNames:hostNames}" `
  --output json

# Force stop if needed
az functionapp stop `
  --resource-group CareerServicesReactApp `
  --name jsearchjobfetch

# Try deletion again
az functionapp delete `
  --resource-group CareerServicesReactApp `
  --name jsearchjobfetch `
  --yes
```

### If VM Deletion Fails

```powershell
# Check VM status and dependencies
az vm show `
  --resource-group CareerServicesReactApp `
  --name career-services-test `
  --query "{Name:name, PowerState:instanceView.statuses[?code=='PowerState'].displayStatus, ProvisioningState:provisioningState}" `
  --output json

# Check for attached resources
az vm show `
  --resource-group CareerServicesReactApp `
  --name career-services-test `
  --query "{NetworkInterfaces:networkProfile.networkInterfaces, DataDisks:storageProfile.dataDisks}" `
  --output json

# Force deallocate if needed
az vm deallocate `
  --resource-group CareerServicesReactApp `
  --name career-services-test `
  --force
```

### If Network Resource Deletion Fails

```powershell
# Check network interface dependencies
az network nic show `
  --resource-group CareerServicesReactApp `
  --name career-services-test967 `
  --query "{Name:name, ProvisioningState:provisioningState, VirtualMachine:id}" `
  --output json

# Check virtual network dependencies
az network vnet show `
  --resource-group CareerServicesReactApp `
  --name career-services-test-vnet `
  --query "{Name:name, Subnets:subnets[].name, ProvisioningState:provisioningState}" `
  --output json
```

### If SQL Server Deletion Fails

```powershell
# List all databases on the server
az sql db list `
  --resource-group CareerServicesReactApp `
  --server cfa-reactdb `
  --query "[].{Name:name, Status:status}" `
  --output table

# Check for firewall rules that might prevent deletion
az sql server firewall-rule list `
  --resource-group CareerServicesReactApp `
  --server cfa-reactdb `
  --output table
```

## Notes

1. **Deletion Order is Critical:**
   - Child resources must be deleted before parent resources
   - Network resources must be deleted in order: VM → NIC → IP/NSG → VNet
   - SQL databases must be deleted before SQL server
   - Function Apps should be stopped before deletion

2. **Dependency Checking:**
   - The script includes checks for unlisted dependencies
   - Always confirm before deleting resources not on the checked list
   - Some resources may have soft-delete enabled (check retention policies)

3. **Timing:**
   - Some deletions may take several minutes to complete
   - Network resource deletions can take 5-10 minutes
   - SQL server deletion may take 10-15 minutes

4. **Irreversible Actions:**
   - All deletions are permanent and cannot be undone
   - Ensure backups are taken before deletion (especially for databases)
   - Verify resource names carefully before executing deletion commands

5. **Cost Impact:**
   - Deleting resources will stop all associated charges
   - Some resources may have retention periods that continue to incur charges
   - Verify deletion completion in Azure Portal

## Script Variables Summary

```powershell
$RESOURCE_GROUP = "CareerServicesReactApp"
$SQL_SERVER = "cfa-reactdb"
$SQL_DATABASE = "vector-search"
$FUNCTION_APP = "jsearchjobfetch"
$VM_NAME = "career-services-test"
$NIC_NAME = "career-services-test967"
$PUBLIC_IP = "career-services-test-ip"
$NSG_NAME = "career-services-test-nsg"
$VNET_NAME = "career-services-test-vnet"
$DISK_NAME = "career-services-test_disk1_6fb85f0f70604bfcb5e8c7317204f1e5"
$SSH_KEY = "career-services-test_key"
$RESTORE_POINT_COLLECTION = "test-server-restore-points"
```

## Execution Checklist

- [ ] Azure CLI installed and configured
- [ ] Logged into Azure with appropriate permissions
- [ ] Verified all checked resources exist in CareerServicesReactApp resource group
- [ ] Reviewed and confirmed resource names match checked items
- [ ] Deleted smart detector alert rules
- [ ] Deleted Function App and Application Insights
- [ ] Deleted AI/Cognitive Services
- [ ] Deleted SQL database and server
- [ ] Deleted VM and all network resources
- [ ] Deleted restore point collection
- [ ] Verified all checked resources are deleted
- [ ] Confirmed no unlisted dependencies remain
- [ ] Documented any issues or remaining resources
