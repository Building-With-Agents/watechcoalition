# WatechProd-v2 VM Configuration Steps

## Connection Information
- **VM Name**: WatechProd-v2
- **Public IP**: 20.106.201.34
- **Admin User**: azwatechadmin
- **SSH Key**: C:\Users\garyl\.ssh\watech_cfa_vm (needs conversion to PPK)
- **Passphrase**: sty7qxmw!

## Prerequisites

### 1. Convert SSH Key to PPK Format
1. Open PuTTYgen
2. Conversions → Import Key
3. Select `C:\Users\garyl\.ssh\watech_cfa_vm`
4. Enter passphrase when prompted: `sty7qxmw!`
5. Click "Save private key"
6. Save as `C:\Users\garyl\.ssh\watech_cfa_vm.ppk`

### 2. Connect via PuTTY
1. Open PuTTY
2. Host Name: `azwatechadmin@20.106.201.34`
3. Connection → SSH → Auth → Browse
4. Select `C:\Users\garyl\.ssh\watech_cfa_vm.ppk`
5. Click "Open"

## Phase 5: Initial VM Configuration

### Step 5.1: System Updates
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 5.2: Configure Swap File (2GB)
```bash
# Create 2GB swap file
sudo fallocate -l 2G /swapfile

# Set proper permissions
sudo chmod 600 /swapfile

# Format as swap
sudo mkswap /swapfile

# Enable swap
sudo swapon /swapfile

# Make it persistent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify swap is active
free -h
swapon --show
```

### Step 5.3: Install and Configure fail2ban
```bash
# Install fail2ban
sudo apt install fail2ban -y

# Create local configuration
sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
findtime = 600
bantime = 3600
EOF

# Enable and start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Verify status
sudo systemctl status fail2ban
sudo fail2ban-client status sshd
```

### Step 5.4: Harden SSH Configuration
```bash
# Backup original config
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Edit SSH configuration
sudo nano /etc/ssh/sshd_config
```

Ensure these settings are set:
```
PasswordAuthentication no
PermitRootLogin no
PubkeyAuthentication yes
MaxAuthTries 3
```

```bash
# Test configuration
sudo sshd -t

# Restart SSH service
sudo systemctl restart sshd
```

**IMPORTANT**: Keep your current SSH session open and test a new connection before closing!

## Phase 6: Install Runtime Stack

### Step 6.1: Install Node.js 22 via NVM
```bash
# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Load NVM
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Install Node.js 22
nvm install 22
nvm alias default 22

# Verify installation
node --version
npm --version
```

### Step 6.2: Install PM2
```bash
# Install PM2 globally
npm install -g pm2

# Verify installation
pm2 --version
```

## Phase 7: Application Deployment

### Step 7.1: Clone Repository
```bash
# Clone the repository
git clone https://CFA1@dev.azure.com/CFA1/Career%20Services/_git/CoalitionWebsite frontend-cfa

# Navigate to directory
cd frontend-cfa
```

### Step 7.2: Update Next.js and Install Dependencies
```bash
# Update Next.js to latest
npm install next@latest

# Install dependencies
npm install

# Verify Next.js version
npm list next

# Build the application
npm run build
```

### Step 7.3: Configure PM2
```bash
# Start application with PM2
pm2 start "npm run start" --name watech

# Save PM2 configuration
pm2 save

# Configure PM2 to start on boot
pm2 startup systemd
# Follow the instructions that PM2 outputs (will ask you to run a sudo command)

# Verify application is running
pm2 status
pm2 logs watech --lines 50

# Test local access
curl -I http://localhost:3000
```

## Phase 8: Nginx Reverse Proxy and SSL Configuration

### Step 8.1: Install Nginx
```bash
# Update package list
sudo apt update

# Install Nginx
sudo apt install nginx -y

# Verify installation
nginx -v
```

### Step 8.2: Create Nginx Configuration File
```bash
# Create Nginx configuration for watechcoalition
sudo nano /etc/nginx/sites-available/watechcoalition
```

Add the following configuration:

```nginx
# HTTP server - redirects to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name www.watechcoalition.org watechcoalition.org;

    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server - main configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.watechcoalition.org watechcoalition.org;

    # SSL certificate paths (will be configured by certbot)
    # ssl_certificate /etc/letsencrypt/live/www.watechcoalition.org/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/www.watechcoalition.org/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy settings for Next.js
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static file caching for Next.js
    location /_next/static/ {
        proxy_pass http://localhost:3000;
        proxy_cache_valid 200 60m;
        add_header Cache-Control "public, immutable";
    }

    # Favicon and static assets
    location ~* \.(ico|jpg|jpeg|png|gif|svg|js|css|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:3000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Client max body size
    client_max_body_size 10M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
```

### Step 8.3: Enable Site Configuration
```bash
# Create symbolic link to enable the site
sudo ln -s /etc/nginx/sites-available/watechcoalition /etc/nginx/sites-enabled/

# Remove default site (optional)
sudo rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t
```

### Step 8.4: Start Nginx
```bash
# Enable Nginx to start on boot
sudo systemctl enable nginx

# Start Nginx
sudo systemctl start nginx

# Check status
sudo systemctl status nginx
```

### Step 8.5: Install Certbot for SSL
```bash
# Install certbot and nginx plugin
sudo apt install certbot python3-certbot-nginx -y

# Verify installation
certbot --version
```

### Step 8.6: Obtain SSL Certificate
**Important**: Verify DNS is working before running this command:
```bash
# Test DNS resolution
nslookup www.watechcoalition.org
nslookup watechcoalition.org
```

Both should return `20.106.201.34`. If they do, proceed:

```bash
# Obtain SSL certificate (interactive)
sudo certbot --nginx -d www.watechcoalition.org -d watechcoalition.org
```

When prompted:
1. Enter your email address
2. Agree to terms of service (Y)
3. Choose whether to share email with EFF (optional)
4. Certbot will automatically configure SSL

### Step 8.7: Verify Auto-Renewal
```bash
# Test certificate renewal (dry run)
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates
```

### Step 8.8: Configure Firewall (if UFW is active)
```bash
# Check if UFW is active
sudo ufw status

# If active, allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
```

### Step 8.9: Final Verification
```bash
# Check Nginx is running
sudo systemctl status nginx

# Check PM2 is running
pm2 status

# Test local connection
curl -I http://localhost:3000

# Test HTTPS from external
curl -I https://www.watechcoalition.org

# Check SSL certificate
openssl s_client -connect www.watechcoalition.org:443 -servername www.watechcoalition.org < /dev/null
```

### Step 8.10: Monitor Logs
```bash
# View Nginx error logs
sudo tail -f /var/log/nginx/error.log

# View Nginx access logs
sudo tail -f /var/log/nginx/access.log

# View PM2 application logs
pm2 logs watech --lines 50
```

## Phase 9: Security Validation

### Step 9.1: Scan for Malicious Processes
```bash
# Check for cryptocurrency miners
ps aux | grep -Ei 'xmrig|hash|c3pool|kernal|ddd'

# Check for suspicious binaries
sudo find / -name 'am64' -o -name 'i386' -o -name 'ddd' -o -name 'xmrig*' -o -name 'kal.tar.gz' 2>/dev/null

# Check for suspicious network connections
sudo netstat -tulpn | grep ESTABLISHED
```

### Step 9.2: Check Cron Jobs
```bash
# List user cron jobs
crontab -l

# List root cron jobs
sudo crontab -l

# Check system cron directories
sudo ls -al /etc/cron.* /etc/cron.d/
```

### Step 9.3: Verify Application Health
```bash
# Check PM2 status
pm2 status

# Test HTTP endpoint
curl -I http://localhost:3000

# Check application logs
pm2 logs watech --lines 100

# Check fail2ban status
sudo fail2ban-client status sshd

# Verify swap is active
free -h
swapon --show
```

## Phase 10: Configure Environment Variables (Optional)

**Note**: This step is optional for the current static site deployment. The site will work without these variables. Add them only if you need Power Platform integration.

### Step 10.1: Configure .env File
```bash
# Navigate to project directory
cd ~/frontend-cfa

# Create .env file
nano .env
```

Add the following (values to be provided as needed):
```
NEXT_PUBLIC_DOMAIN=www.watechcoalition.org
NEXT_PUBLIC_TENANT_ID=a3c7a257-40f2-43a9-9373-8bb5fc6862f7
NEXT_PUBLIC_CLIENT_ID=dfc4e746-44b7-420b-8463-ad6011728b8d
NEXT_PUBLIC_BASE_URL=https://cfahelpdesksandbox.api.crm.dynamics.com/api/data/v9.1
NEXT_PUBLIC_TOKEN_SCOPE=https://cfahelpdesksandbox.crm.dynamics.com/.default
CP_APPLICATION_ENDPOINT=<provide-value>
AI_DEV_ENDPOINT=<provide-value>
```

```bash
# Set proper permissions
chmod 600 .env

# Restart PM2 to load new environment variables
pm2 restart watech

# Verify application starts
pm2 logs watech --lines 50
```

## Phase 11: Final Verification

Run these commands to verify everything:

```bash
# System information
uname -a
free -h
df -h

# Node.js and PM2
node --version
npm --version
pm2 --version

# Services
sudo systemctl status fail2ban
sudo systemctl status ssh

# Application
pm2 status
pm2 logs watech --lines 20
curl -I http://localhost:3000

# Security checks
sudo fail2ban-client status
ps aux | grep -v grep | grep -E 'pm2|node'
```

## Phase 12: Repository Sync and Documentation

### Step 12.1: Create Future Reinstatement Documentation (LOCAL MACHINE)

**This step should be done on your LOCAL Windows machine**, not on the VM.

1. In your local workspace: `C:\Users\garyl\repos\cfa-projects\frontend-cfa`
2. Create the file `docs/FUTURE_REINSTATEMENT.md` with the following content:

```markdown
# Future Reinstatement Documentation

## Database Configuration (Currently Unused)
When reinstating database functionality, rotate these secrets:
- `MSSQL_CONNECTION_STRING=` (leave blank - will need rotation)
- `DATABASE_URL=` (leave blank - will need rotation)

## Authentication Providers (Currently Unused)
When reinstating authentication, rotate these secrets:
- `AUTH_SECRET=` (leave blank - will need rotation)
- `AUTH_GITHUB_ID=` (keep ID, rotate secret)
- `AUTH_GITHUB_SECRET=` (leave blank - will need rotation)
- `NEXTAUTH_SECRET=` (leave blank - will need rotation)
- `NEXTAUTH_SALT=` (leave blank - will need rotation)
- `GOOGLE_CLIENT_ID=` (keep ID, rotate secret)
- `GOOGLE_CLIENT_SECRET=` (leave blank - will need rotation)
- `AUTH_MICROSOFT_ENTRA_ID_ID=` (keep ID, rotate secret)
- `AUTH_MICROSOFT_ENTRA_ID_SECRET=` (leave blank - will need rotation)
- `AUTH_MICROSOFT_ENTRA_ID_TENANT_ID=` (keep: common)

## Azure Storage (Currently Unused)
When reinstating Azure Storage functionality, rotate these secrets:
- `AZURE_STORAGE_CONNECTION_STRING=` (leave blank - will need rotation)
- `AZURE_STORAGE_ACCOUNT_KEY=` (leave blank - will need rotation)
- `AZURE_STORAGE_ACCOUNT_NAME=` (keep: careerservicesstorage)

## Azure OpenAI (Currently Unused)
When reinstating Azure OpenAI functionality, rotate these secrets:
- `AZURE_OPENAI_ENDPOINT=` (https://eastus.api.cognitive.microsoft.com/)
- `AZURE_OPENAI_API_KEY=` (generate new - revoke old)
- `AZURE_OPENAI_API_VERSION=` (2025-01-01-preview)
- `AZURE_OPENAI_DEPLOYMENT_NAME=` (gpt-4.1-mini)

## Azure OpenAI Embeddings (Currently Unused)
When reinstating Azure OpenAI Embeddings functionality, rotate these secrets:
- `AZURE_OPENAI_EMBEDDING_ENDPOINT=` (https://eastus.api.cognitive.microsoft.com/)
- `AZURE_OPENAI_EMBEDDING_API_KEY=` (generate new - revoke old)
- `AZURE_OPENAI_EMBEDDING_API_VERSION=` (2024-02-01)
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=` (text-embedding-3-small)

## Important Notes
- **ALL secrets must be rotated** when reinstating these features
- Do NOT reuse old compromised secrets
- Document all service links for credential rotation
- Test thoroughly in a development environment first
```

### Step 12.2: Commit and Push Changes (LOCAL MACHINE)

```powershell
# On your local Windows machine
cd C:\Users\garyl\repos\cfa-projects\frontend-cfa

# Add the new file
git add docs/FUTURE_REINSTATEMENT.md

# Commit with descriptive message
git commit -m "Add future reinstatement documentation for disabled features"

# Push to Azure DevOps
git push origin main
```

### Step 12.3: Pull Updates on VM

```bash
# SSH back into the VM
# Navigate to the project directory
cd ~/frontend-cfa

# Pull the latest changes from the repository
git pull origin main

# Verify the file was pulled
ls -la docs/FUTURE_REINSTATEMENT.md
cat docs/FUTURE_REINSTATEMENT.md

# Restart the application to ensure everything is in sync
pm2 restart watech
pm2 logs watech --lines 20
```

## Troubleshooting

### Nginx Issues
```bash
# Restart Nginx
sudo systemctl restart nginx

# Check what's listening on ports
sudo netstat -tulpn | grep -E ':80|:443|:3000'

# Test Nginx config syntax
sudo nginx -t

# View detailed error logs
sudo tail -100 /var/log/nginx/error.log
```

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Manually renew certificate
sudo certbot renew

# Force certificate renewal
sudo certbot renew --force-renewal
```

### DNS Issues
```bash
# Test DNS resolution
dig www.watechcoalition.org
dig watechcoalition.org

# Check from external DNS
nslookup www.watechcoalition.org 8.8.8.8
```

### Application Not Responding
```bash
# Check PM2 status
pm2 status
pm2 logs watech --lines 100

# Restart application
pm2 restart watech

# Check if port 3000 is in use
sudo lsof -i :3000
```

## Completion Checklist
- [ ] Swap file created and active (2GB)
- [ ] fail2ban installed and running
- [ ] SSH hardened (no password auth, no root login)
- [ ] Node.js 22.x installed
- [ ] PM2 installed and configured
- [ ] Application cloned and built
- [ ] PM2 running application successfully
- [ ] .env file configured with proper permissions
- [ ] Nginx installed and configured
- [ ] SSL certificate obtained and installed
- [ ] HTTPS working for www and non-www domains
- [ ] HTTP redirects to HTTPS
- [ ] No malicious processes detected
- [ ] No suspicious cron jobs
- [ ] Application responding on localhost
- [ ] Site accessible at https://www.watechcoalition.org
- [ ] All security checks passed
- [ ] Future reinstatement documentation created locally
- [ ] Changes committed and pushed to Azure DevOps
- [ ] VM repository synced with latest changes

