# Accessing Azure File Share Contents

## Overview

This guide explains how to view and access files in Azure File Shares, specifically for the storage account `stwaifinderpilot` and the `student-envs` file share.

## Method 1: Azure Portal - Storage Browser (Easiest)

### Steps:

1. **Navigate to Storage Browser:**
   - In Azure Portal, go to your storage account: `stwaifinderpilot`
   - In the left menu, under **"Data storage"**, click **"Storage browser"**
   - Click **"File shares"** in the Storage browser
   - Click on **"student-envs"** to browse

2. **Browse Files:**
   - You'll see folders and files in a tree view
   - Click folders to expand them
   - Right-click files to download, delete, or view properties
   - Use the upload button to add files

**Note:** This is the simplest method but may be slower for large file structures.

## Method 2: Azure Storage Explorer (Desktop App - Recommended)

### Installation:

1. **Download Azure Storage Explorer:**
   - Visit: https://azure.microsoft.com/features/storage-explorer/
   - Or download directly: https://azure.microsoft.com/products/storage/storage-explorer/
   - Install the application

2. **Connect to Storage Account:**
   - Open Azure Storage Explorer
   - Click **"Add an account"** or **"Connect"**
   - Sign in with your Azure account
   - Your storage accounts will appear automatically

3. **Browse File Share:**
   - Expand **"Storage Accounts"**
   - Expand **"stwaifinderpilot"**
   - Expand **"File Shares"**
   - Click **"student-envs"** to view contents
   - Navigate folders like a file explorer

**Advantages:**
- Fast file browsing
- Drag-and-drop upload/download
- Better for large file structures
- Can copy/paste files easily

## Method 3: Azure CLI

### Prerequisites:

```powershell
# Install Azure CLI if not already installed
# Download from: https://aka.ms/installazurecliwindows

# Login to Azure
az login

# Set subscription (if multiple)
az account set --subscription "<subscription-id>"
```

### List Files in File Share:

```powershell
# List files in the root of the file share
az storage file list `
  --share-name student-envs `
  --account-name stwaifinderpilot `
  --output table

# List files in a specific directory
az storage file list `
  --share-name student-envs `
  --account-name stwaifinderpilot `
  --path "folder/subfolder" `
  --output table

# Get detailed information about files
az storage file list `
  --share-name student-envs `
  --account-name stwaifinderpilot `
  --output json
```

### Download Files:

```powershell
# Download a single file
az storage file download `
  --share-name student-envs `
  --account-name stwaifinderpilot `
  --path "path/to/file.txt" `
  --dest "C:\local\path\file.txt"

# Download entire directory (recursive)
az storage file download-batch `
  --source student-envs `
  --destination "C:\local\folder" `
  --account-name stwaifinderpilot
```

### Upload Files:

```powershell
# Upload a single file
az storage file upload `
  --share-name student-envs `
  --account-name stwaifinderpilot `
  --source "C:\local\file.txt" `
  --path "remote/path/file.txt"

# Upload entire directory
az storage file upload-batch `
  --source "C:\local\folder" `
  --destination student-envs `
  --account-name stwaifinderpilot
```

### Get Storage Account Key (if needed):

```powershell
# Get storage account keys
az storage account keys list `
  --resource-group "<resource-group-name>" `
  --account-name stwaifinderpilot

# Use key for authentication
$STORAGE_KEY = "<storage-account-key>"
az storage file list `
  --share-name student-envs `
  --account-name stwaifinderpilot `
  --account-key $STORAGE_KEY
```

## Method 4: Mount as Network Drive (Windows)

### Using Storage Account Key:

1. **Get Storage Account Key:**
   - Azure Portal → Storage account → **"Access keys"**
   - Copy **"key1"** or **"key2"**

2. **Map Network Drive:**
   ```powershell
   # Format: \\<storage-account-name>.file.core.windows.net\<file-share-name>
   net use Z: \\stwaifinderpilot.file.core.windows.net\student-envs /user:Azure\stwaifinderpilot <storage-account-key>
   ```

3. **Browse in File Explorer:**
   - Open File Explorer
   - Navigate to **Z:** drive (or whatever letter you mapped)
   - Browse files like a local drive

### Using Azure AD Authentication (More Secure):

```powershell
# Connect using Azure AD (requires Azure AD authentication configured)
# First, ensure identity-based access is configured in Azure Portal

# Map drive with Azure AD
net use Z: \\stwaifinderpilot.file.core.windows.net\student-envs /user:AzureAD\<your-email>
```

**Note:** Identity-based access must be configured in Azure Portal first.

## Method 5: PowerShell Script for Quick Access

Create a PowerShell script to quickly browse file shares:

```powershell
# Save as Browse-AzureFileShare.ps1

param(
    [string]$StorageAccount = "stwaifinderpilot",
    [string]$FileShare = "student-envs",
    [string]$Path = ""
)

# Login if not already
$context = az account show 2>$null
if (-not $context) {
    Write-Host "Logging into Azure..."
    az login
}

# List files
if ($Path) {
    Write-Host "Listing files in: $Path" -ForegroundColor Cyan
    az storage file list `
        --share-name $FileShare `
        --account-name $StorageAccount `
        --path $Path `
        --output table
} else {
    Write-Host "Listing files in root:" -ForegroundColor Cyan
    az storage file list `
        --share-name $FileShare `
        --account-name $StorageAccount `
        --output table
}
```

**Usage:**
```powershell
# List root files
.\Browse-AzureFileShare.ps1

# List files in a folder
.\Browse-AzureFileShare.ps1 -Path "folder/subfolder"
```

## Method 6: Python Script (Using Azure SDK)

If you need programmatic access:

```python
from azure.storage.fileshare import ShareClient
from azure.core.credentials import AzureNamedKeyCredential

# Get storage account key from Azure Portal
account_name = "stwaifinderpilot"
account_key = "<your-storage-account-key>"
share_name = "student-envs"

# Create credential and client
credential = AzureNamedKeyCredential(account_name, account_key)
share_client = ShareClient(
    account_url=f"https://{account_name}.file.core.windows.net",
    share_name=share_name,
    credential=credential
)

# List files and directories
def list_files(path=""):
    items = share_client.list_directories_and_files(directory_name=path)
    for item in items:
        if item.is_directory:
            print(f"[DIR]  {item.name}/")
        else:
            print(f"[FILE] {item.name} ({item.size} bytes)")

# List root
print("Root directory:")
list_files()

# List subdirectory
print("\nSubdirectory:")
list_files("folder/subfolder")
```

## Quick Reference: Finding Storage Account Information

### Get Storage Account Details:

```powershell
# List all storage accounts
az storage account list --output table

# Get specific storage account details
az storage account show `
  --name stwaifinderpilot `
  --resource-group "<resource-group-name>" `
  --output json

# Get file share details
az storage share show `
  --name student-envs `
  --account-name stwaifinderpilot `
  --output json
```

### Get Connection String:

```powershell
# Get connection string (useful for applications)
az storage account show-connection-string `
  --name stwaifinderpilot `
  --resource-group "<resource-group-name>"
```

## Security Best Practices

1. **Use Azure AD Authentication** instead of storage account keys when possible
2. **Use SAS tokens** for temporary access instead of sharing keys
3. **Enable soft delete** (already configured: 7 days)
4. **Use identity-based access** for better security
5. **Rotate storage account keys** regularly
6. **Limit access** using Azure RBAC roles

## Troubleshooting

### Cannot Access File Share

1. **Check permissions:**
   - Verify you have "Storage File Data SMB Share Contributor" or similar role
   - Check if identity-based access is configured

2. **Check network connectivity:**
   - Ensure port 445 (SMB) is not blocked by firewall
   - For Azure AD auth, ensure network allows Azure AD authentication

3. **Verify storage account key:**
   ```powershell
   az storage account keys list `
     --resource-group "<resource-group-name>" `
     --account-name stwaifinderpilot
   ```

### Files Not Showing

1. **Check path:**
   - Ensure path is correct (case-sensitive)
   - Use forward slashes `/` not backslashes `\`

2. **Check permissions:**
   - Verify you have read access to the file share
   - Check if files are in subdirectories

3. **Refresh:**
   - In Azure Portal, click "Refresh"
   - In Storage Explorer, right-click and "Refresh"

## Recommended Approach

For **quick browsing**: Use **Azure Storage Explorer** (Method 2)  
For **automation/scripts**: Use **Azure CLI** (Method 3)  
For **Windows file access**: **Mount as network drive** (Method 4)  
For **web-based access**: Use **Azure Portal Storage Browser** (Method 1)


