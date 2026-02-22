# Installing Docker

This guide covers installing Docker for Windows, macOS, and Linux. The app uses Docker to run SQL Server locally.

## Verify Installation

After installing, verify:

```bash
docker --version
docker compose version
```

---

## Windows

### Docker Desktop for Windows

1. Download [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Run the installer
3. Enable **WSL 2** when prompted (recommended)
4. Restart if required
5. Launch Docker Desktop from the Start menu

### WSL 2 Backend (Recommended)

Docker Desktop uses WSL 2 by default on recent Windows versions. Ensure WSL 2 is installed:

```powershell
wsl --update
```

### Troubleshooting (Windows)

| Issue | Solution |
|-------|----------|
| "Docker Desktop failed to start" | Ensure virtualization is enabled in BIOS; enable Hyper-V or WSL 2 |
| WSL 2 not found | Run `wsl --install` in an elevated PowerShell |
| Port conflicts | Check that port 1433 (SQL) is not in use: `netstat -an | findstr :1433` |

---

## macOS

### Docker Desktop for Mac

1. Download [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - **Apple Silicon (M1/M2/M3):** Choose "Mac with Apple chip"
   - **Intel:** Choose "Mac with Intel chip"
2. Open the `.dmg` and drag Docker to Applications
3. Launch Docker from Applications
4. Grant permissions when prompted (e.g. for networking)

### Troubleshooting (macOS)

| Issue | Solution |
|-------|----------|
| "Cannot connect to the Docker daemon" | Ensure Docker Desktop is running (menu bar icon) |
| Resource limits | Increase memory/CPU in Docker Desktop → Settings → Resources |
| Port 1433 in use | Change `MSSQL_PORT` in `.env.docker` |

---

## Linux

### Docker Engine + Docker Compose Plugin

Most Linux distributions use the Docker Engine with the Compose plugin.

#### Debian / Ubuntu

```bash
# Add Docker's official GPG key
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Compose plugin
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add your user to the docker group (to run without sudo)
sudo usermod -aG docker $USER
# Log out and back in for group membership to take effect
```

#### Fedora / RHEL / CentOS

```bash
# Add Docker repository
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo

# Install Docker Engine and Compose plugin
sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Troubleshooting (Linux)

| Issue | Solution |
|-------|----------|
| "permission denied" when running docker | Add user to `docker` group: `sudo usermod -aG docker $USER`; log out and back in |
| "Cannot connect to the Docker daemon" | Start Docker: `sudo systemctl start docker` |
| SELinux on RHEL/Fedora | If encountering permission errors, consider `setenforce 0` temporarily for testing (not for production) |

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SQL Server on Docker](https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker)
