#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_server.sh  –  EC2 Ubuntu 22.04 server hardening + app setup
# Run as:  sudo bash setup_server.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail
log() { echo ">>> $*"; }

# ── System update ─────────────────────────────────────────────────────────────
log "Updating system packages…"
apt-get update -y && apt-get upgrade -y

# ── Install dependencies ──────────────────────────────────────────────────────
log "Installing Docker, Nginx, Fail2ban, CloudWatch Agent…"
apt-get install -y curl git unzip nginx fail2ban ufw logrotate awscli

# Docker
curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
systemctl enable docker && systemctl start docker

# Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# CloudWatch Agent
wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i amazon-cloudwatch-agent.deb && rm amazon-cloudwatch-agent.deb

# ── SSH hardening ─────────────────────────────────────────────────────────────
log "Hardening SSH…"
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/'          /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#Port 22/Port 22/'                              /etc/ssh/sshd_config
echo "MaxAuthTries 3" >> /etc/ssh/sshd_config
systemctl restart sshd

# ── Fail2ban ──────────────────────────────────────────────────────────────────
log "Configuring Fail2ban…"
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = 22
logpath = /var/log/auth.log

[nginx-http-auth]
enabled  = true
port     = http,https
logpath  = /var/log/nginx/error.log
EOF
systemctl enable fail2ban && systemctl restart fail2ban

# ── UFW firewall ──────────────────────────────────────────────────────────────
log "Configuring UFW firewall…"
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw --force enable

# ── Logrotate for app logs ────────────────────────────────────────────────────
cat > /etc/logrotate.d/ecommerce << 'EOF'
/var/log/ecommerce/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload nginx 2>/dev/null || true
    endscript
}
EOF

# ── Deploy app ────────────────────────────────────────────────────────────────
log "Cloning application…"
mkdir -p /opt/ecommerce-devsecops
git clone https://github.com/YOUR_USERNAME/ecommerce-devsecops.git /opt/ecommerce-devsecops
cd /opt/ecommerce-devsecops
cp .env.example .env
# IMPORTANT: Edit /opt/ecommerce-devsecops/.env with your real values before starting

# ── Install Nginx config ──────────────────────────────────────────────────────
cp config/nginx.conf /etc/nginx/sites-available/ecommerce
ln -sf /etc/nginx/sites-available/ecommerce /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ── Backup cron ──────────────────────────────────────────────────────────────
log "Setting up backup cron job…"
chmod +x scripts/backup.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/ecommerce-devsecops/scripts/backup.sh >> /var/log/ecommerce/backup.log 2>&1") | crontab -

log "Setup complete. Edit /opt/ecommerce-devsecops/.env then run: docker-compose up -d"
