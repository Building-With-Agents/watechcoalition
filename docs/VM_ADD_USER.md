# Adding a New User to WatechProd-v2 VM

## Overview

This guide explains how to create a new user account on WatechProd-v2 and configure SSH access for them. Since the VM has password authentication disabled (for security), the new user must use SSH key authentication.

## Prerequisites

- You must be logged in as `azwatechadmin` (or another user with sudo privileges)
- The new user must have an SSH key pair (or be able to generate one)
- Access to the VM via SSH

## Step 1: Create the New User Account

SSH into the VM as the admin user, then run:

```bash
# Create new user (replace 'newusername' with desired username)
sudo adduser newusername

# You'll be prompted to:
# - Enter a password (can be temporary, won't be used for SSH)
# - Enter full name (optional)
# - Enter room number, work phone, etc. (all optional, press Enter to skip)
```

**Note:** The password you set here won't be used for SSH login since password authentication is disabled. It's only needed for sudo operations if the user gets sudo privileges.

## Step 2: Add User to Sudo Group (Optional)

If the new user needs administrative privileges:

```bash
# Add user to sudo group
sudo usermod -aG sudo newusername

# Verify the user was added
groups newusername
```

**Security Note:** Only grant sudo access if the user actually needs it. For most users, regular user privileges are sufficient.

## Step 3: Set Up SSH Key Authentication

Since password authentication is disabled, the new user must use SSH keys. There are two approaches:

### Option A: User Provides Their Public Key (Recommended)

**On the new user's local machine**, they should:

1. **Check if they already have an SSH key:**
   ```bash
   # On Windows (Git Bash or WSL)
   ls ~/.ssh/id_*.pub
   
   # On Linux/Mac
   ls ~/.ssh/id_*.pub
   ```

2. **If no key exists, generate one:**
   ```bash
   # Generate ED25519 key (recommended, more secure)
   ssh-keygen -t ed25519 -C "their_email@example.com"
   
   # Or generate RSA key (if ED25519 not supported)
   ssh-keygen -t rsa -b 4096 -C "their_email@example.com"
   ```

3. **Copy their public key:**
   ```bash
   # Display the public key (they should copy this)
   cat ~/.ssh/id_ed25519.pub
   # or
   cat ~/.ssh/id_rsa.pub
   ```

**On the VM (as admin user):**

```bash
# Switch to the new user's home directory
sudo su - newusername

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Create authorized_keys file
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Add their public key (paste the key they provided)
nano ~/.ssh/authorized_keys
# Paste their public key, save and exit (Ctrl+X, Y, Enter)

# Verify permissions are correct
ls -la ~/.ssh/

# Exit back to admin user
exit
```

### Option B: Generate Key Pair on VM (Less Secure)

If the user doesn't have a key pair, you can generate one on the VM:

```bash
# Switch to new user
sudo su - newusername

# Generate SSH key pair
ssh-keygen -t ed25519 -C "newusername@watechprod-v2"
# Press Enter to accept default location
# Enter a passphrase (recommended) or leave empty

# The public key will be in ~/.ssh/id_ed25519.pub
# The private key will be in ~/.ssh/id_ed25519

# Set up authorized_keys (for testing)
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Display the private key (user needs to copy this securely)
cat ~/.ssh/id_ed25519

exit
```

**⚠️ Security Warning:** If you use Option B, the private key will be visible in terminal history. The user should:
1. Copy the private key securely
2. Save it to their local machine
3. Delete it from the VM after copying
4. Change the key passphrase

## Step 4: Verify SSH Configuration

Ensure SSH is configured to allow the new user:

```bash
# Check SSH configuration
sudo cat /etc/ssh/sshd_config | grep -E "PasswordAuthentication|PubkeyAuthentication|PermitRootLogin"

# Should show:
# PasswordAuthentication no
# PubkeyAuthentication yes
# PermitRootLogin no
```

If these settings are correct, the new user should be able to connect.

## Step 5: Test the Connection

**From the new user's local machine:**

```bash
# Test SSH connection
ssh newusername@20.106.201.34

# If using a specific key file:
ssh -i ~/.ssh/id_ed25519 newusername@20.106.201.34
```

**On Windows with PuTTY:**

1. Convert the private key to PPK format using PuTTYgen
2. In PuTTY:
   - Host Name: `newusername@20.106.201.34`
   - Connection → SSH → Auth → Browse
   - Select the PPK file
   - Click Open

## Step 6: Set Up User Environment (Optional)

If the user needs access to Node.js, PM2, or other tools:

```bash
# Switch to new user
sudo su - newusername

# If Node.js was installed via NVM (as azwatechadmin)
# Option 1: Install NVM for the new user
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm install 22
nvm alias default 22

# Option 2: Share NVM installation (if both users need it)
# This requires setting up shared NVM directory - more complex

# Install PM2 globally (if needed)
npm install -g pm2

exit
```

## Step 7: Configure User-Specific Settings

### Set Up Git (if user needs to work with repository)

```bash
sudo su - newusername

# Configure git
git config --global user.name "User Full Name"
git config --global user.email "user@example.com"

# If they need to clone the repository
# They'll need Azure DevOps credentials or SSH key set up in Azure DevOps

exit
```

### Set Up Shell Environment

```bash
sudo su - newusername

# Edit bashrc or zshrc
nano ~/.bashrc

# Add any custom aliases or environment variables
# Example:
# alias ll='ls -alF'
# export EDITOR=nano

# Reload shell configuration
source ~/.bashrc

exit
```

## Security Best Practices

### 1. Limit User Permissions

Only grant the minimum permissions needed:

```bash
# Check current user groups
groups newusername

# Remove from sudo group if not needed
sudo deluser newusername sudo

# Verify removal
groups newusername
```

### 2. Monitor User Activity

```bash
# View user login history
last newusername

# Check current logged-in users
who

# View user's command history (if they're currently logged in)
sudo su - newusername
history
```

### 3. Set Up User-Specific fail2ban (Optional)

fail2ban is already protecting SSH globally, but you can add user-specific monitoring:

```bash
# View fail2ban status
sudo fail2ban-client status sshd

# Check if user is banned
sudo fail2ban-client status sshd | grep newusername
```

### 4. Regular Key Rotation

Periodically review and rotate SSH keys:

```bash
# View authorized keys for user
sudo cat /home/newusername/.ssh/authorized_keys

# Remove old keys if needed
sudo nano /home/newusername/.ssh/authorized_keys
# Delete the line with the old key
```

## Troubleshooting

### User Cannot Connect

1. **Check SSH service:**
   ```bash
   sudo systemctl status sshd
   ```

2. **Check user's authorized_keys:**
   ```bash
   sudo cat /home/newusername/.ssh/authorized_keys
   sudo ls -la /home/newusername/.ssh/
   ```

3. **Check permissions:**
   ```bash
   # .ssh directory should be 700
   sudo chmod 700 /home/newusername/.ssh
   
   # authorized_keys should be 600
   sudo chmod 600 /home/newusername/.ssh/authorized_keys
   ```

4. **Check SSH logs:**
   ```bash
   sudo tail -f /var/log/auth.log
   # Try connecting and watch for errors
   ```

5. **Verify user account exists:**
   ```bash
   id newusername
   ```

### User Needs Sudo Access

```bash
# Add to sudo group
sudo usermod -aG sudo newusername

# Verify
groups newusername
# Should show: newusername sudo

# Test sudo access (as the new user)
sudo su - newusername
sudo whoami
# Should output: root
```

### User Locked Out

If a user is locked out and you need to reset their access:

```bash
# Remove their old authorized_keys
sudo rm /home/newusername/.ssh/authorized_keys

# Create new one
sudo mkdir -p /home/newusername/.ssh
sudo touch /home/newusername/.ssh/authorized_keys
sudo chmod 700 /home/newusername/.ssh
sudo chmod 600 /home/newusername/.ssh/authorized_keys
sudo chown -R newusername:newusername /home/newusername/.ssh

# Add their new public key
sudo nano /home/newusername/.ssh/authorized_keys
```

## Removing a User

If you need to remove a user account:

```bash
# Lock the user account (prevents login)
sudo usermod -L newusername

# Or delete the user account entirely
sudo deluser newusername

# Remove user's home directory (optional)
sudo rm -r /home/newusername

# Remove user from sudo group (if they had it)
sudo deluser newusername sudo
```

## Quick Reference

### Create User with SSH Key (One-Liner)

```bash
# Replace 'newusername' and paste their public key
NEW_USER="newusername"
PUBLIC_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... user@example.com"

sudo adduser --disabled-password --gecos "" $NEW_USER
sudo mkdir -p /home/$NEW_USER/.ssh
echo "$PUBLIC_KEY" | sudo tee /home/$NEW_USER/.ssh/authorized_keys
sudo chmod 700 /home/$NEW_USER/.ssh
sudo chmod 600 /home/$NEW_USER/.ssh/authorized_keys
sudo chown -R $NEW_USER:$NEW_USER /home/$NEW_USER/.ssh
```

### List All Users with SSH Access

```bash
# List all users with .ssh directories
sudo find /home -name ".ssh" -type d 2>/dev/null

# List all users with authorized_keys
sudo find /home -name "authorized_keys" -type f 2>/dev/null | xargs -I {} sh -c 'echo "User: $(dirname $(dirname {}))"; cat {}'
```

## Summary

1. ✅ Create user account: `sudo adduser newusername`
2. ✅ Add to sudo group (if needed): `sudo usermod -aG sudo newusername`
3. ✅ Set up SSH key: Add public key to `~/.ssh/authorized_keys`
4. ✅ Set correct permissions: `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/authorized_keys`
5. ✅ Test connection: `ssh newusername@20.106.201.34`

**Important:** Since password authentication is disabled, SSH key authentication is the only way to connect. Make sure the user has their private key and knows how to use it.



