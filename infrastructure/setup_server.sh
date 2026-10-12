#!/usr/bin/env bash
# Server Provisioning Script for Hetzner CX22 (Ubuntu 24.04 LTS)
# Ad-to-Sale Attribution System

set -euo pipefail

echo "=========================================================="
echo " PROVISIONING N8N ATTRIBUTION SERVER ON UBUNTU 24.04"
echo "=========================================================="

# 1. Update and upgrade OS packages
echo "[+] Updating system packages..."
apt-get update && apt-get upgrade -y
apt-get install -y curl ufw git jq fail2ban

# 2. Configure UFW firewall
echo "[+] Configuring firewall (UFW)..."
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP Let\'s Encrypt'
ufw allow 443/tcp comment 'HTTPS Traefik'
ufw --force enable

# 3. Install Docker Engine and Compose plugin
if ! command -v docker &> /dev/null; then
    echo "[+] Installing Docker Engine..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "[*] Docker is already installed."
fi

# 4. Create n8n app directory
APP_DIR="/opt/n8n"
echo "[+] Setting up application directory: ${APP_DIR}..."
mkdir -p "${APP_DIR}"

# 5. Check for docker-compose.yml and .env
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml "${APP_DIR}/"
fi
if [ -f ".env.example" ] && [ ! -f "${APP_DIR}/.env" ]; then
    cp .env.example "${APP_DIR}/.env"
    echo "[!] Template copied to ${APP_DIR}/.env. Please edit this file with your real domain and email."
fi

cd "${APP_DIR}"

echo "=========================================================="
echo " SERVER READY!"
echo " Next steps:"
echo "   1. Point DNS A-record (e.g. n8n.homecartel.ph) -> Server Public IP"
echo "   2. Edit /opt/n8n/.env with your DOMAIN_NAME and SSL_EMAIL"
echo "   3. Run: cd /opt/n8n && docker compose up -d"
echo "   4. Open https://n8n.yourdomain.com in browser to create owner account"
echo "=========================================================="
