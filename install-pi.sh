#!/bin/bash
################################################################################
# Fire Department Intranet - Raspberry Pi 5 Auto-Installer
# One-command deployment for Raspberry Pi 5
# 
# Usage: curl -sSL https://raw.githubusercontent.com/thegspiro/fd-intranet/main/install-pi.sh | sudo bash
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
print_status() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_info() { echo -e "${BLUE}[i]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

# Banner
clear
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🚒  Fire Department Intranet - Pi 5 Installer  🚒      ║
║                                                           ║
║   Automated deployment for Raspberry Pi 5                ║
║   Installation time: ~15 minutes                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF

echo ""
print_info "Starting installation..."
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Check if Raspberry Pi
if [ ! -f /proc/cpuinfo ]; then
    print_error "Cannot detect system type"
    exit 1
fi

if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    print_warning "This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Detect Pi model
if grep -q "Raspberry Pi 5" /proc/cpuinfo; then
    PI_MODEL="Pi 5"
    RECOMMENDED_WORKERS=3
elif grep -q "Raspberry Pi 4" /proc/cpuinfo; then
    PI_MODEL="Pi 4"
    RECOMMENDED_WORKERS=2
else
    PI_MODEL="Unknown"
    RECOMMENDED_WORKERS=2
    print_warning "Detected $PI_MODEL - optimizing for Pi 4 settings"
fi

print_info "Detected: Raspberry $PI_MODEL"
echo ""

# Get configuration
echo ""
print_info "Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "Domain/hostname [fdintranet.local]: " DOMAIN
DOMAIN=${DOMAIN:-fdintranet.local}

read -p "Admin email address: " ADMIN_EMAIL
while [[ ! "$ADMIN_EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; do
    print_error "Invalid email format"
    read -p "Admin email address: " ADMIN_EMAIL
done

read -sp "Django admin password: " ADMIN_PASSWORD
echo ""
while [[ ${#ADMIN_PASSWORD} -lt 8 ]]; do
    print_error "Password must be at least 8 characters"
    read -sp "Django admin password: " ADMIN_PASSWORD
    echo ""
done

read -p "Department name [Fire Department]: " DEPT_NAME
DEPT_NAME=${DEPT_NAME:-Fire Department}

# Generate secrets
print_info "Generating secure credentials..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)

echo ""
print_status "Configuration complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Update system
print_info "Step 1/10: Updating system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq 2>&1 | grep -v "^Get:" | grep -v "^Ign:" || true
apt-get upgrade -y -qq 2>&1 | grep -v "^Get:" | grep -v "^Ign:" || true
print_status "System updated"

# Install dependencies
print_info "Step 2/10: Installing dependencies (~5 minutes)..."
apt-get install -y -qq \
    python3-full \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    supervisor \
    ufw \
    build-essential \
    libpq-dev \
    python3-dev \
    curl \
    htop \
    iotop \
    vim 2>&1 | grep -v "^Selecting" | grep -v "^Preparing" | grep -v "^Unpacking" || true

print_status "Dependencies installed"

# Configure PostgreSQL
print_info "Step 3/10: Setting up database..."
systemctl start postgresql
systemctl enable postgresql >/dev/null 2>&1

# Create database and user
sudo -u postgres psql << PGSQL >/dev/null 2>&1
DROP DATABASE IF EXISTS fd_intranet;
DROP USER IF EXISTS fdapp;
CREATE DATABASE fd_intranet;
CREATE USER fdapp WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE fdapp SET client_encoding TO 'utf8';
ALTER ROLE fdapp SET default_transaction_isolation TO 'read committed';
ALTER ROLE fdapp SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE fd_intranet TO fdapp;
PGSQL

# Optimize PostgreSQL for Pi
PG_VERSION=$(ls /etc/postgresql/ | head -1)
PG_CONF_DIR="/etc/postgresql/$PG_VERSION/main"

cat > "$PG_CONF_DIR/conf.d/pi-optimization.conf" << PGCONF
# Raspberry $PI_MODEL Optimizations
shared_buffers = 1GB
effective_cache_size = 2GB
maintenance_work_mem = 128MB
work_mem = 4MB
max_connections = 50
wal_buffers = 8MB
checkpoint_completion_target = 0.9
random_page_cost = 1.1
effective_io_concurrency = 200
log_min_duration_statement = 5000
PGCONF

systemctl restart postgresql
print_status "Database configured"

# Create application user
print_info "Step 4/10: Creating application user..."
if id "fdapp" &>/dev/null; then
    print_warning "User fdapp already exists, skipping..."
else
    useradd -r -s /bin/bash -d /opt/fd-intranet -m fdapp
fi
print_status "Application user ready"

# Clone repository
print_info "Step 5/10: Downloading application..."
if [ -d "/opt/fd-intranet/app" ]; then
    print_warning "Application directory exists, removing..."
    rm -rf /opt/fd-intranet/app
fi

sudo -u fdapp git clone --quiet https://github.com/thegspiro/fd-intranet.git /opt/fd-intranet/app
cd /opt/fd-intranet/app
print_status "Application downloaded"

# Set up Python environment
print_info "Step 6/10: Setting up Python environment (~3 minutes)..."
sudo -u fdapp python3 -m venv /opt/fd-intranet/app/venv

# Upgrade pip quietly
sudo -u fdapp /opt/fd-intranet/app/venv/bin/pip install --quiet --upgrade pip setuptools wheel

# Install requirements
sudo -u fdapp /opt/fd-intranet/app/venv/bin/pip install --quiet -r requirements.txt
sudo -u fdapp /opt/fd-intranet/app/venv/bin/pip install --quiet gunicorn psycopg2-binary

print_status "Python environment ready"

# Create .env file
print_info "Step 7/10: Creating configuration..."
cat > /opt/fd-intranet/app/.env << ENVFILE
# Auto-generated by installer on $(date)
SECRET_KEY='$SECRET_KEY'
DEBUG=False
ALLOWED_HOSTS='$DOMAIN,localhost,127.0.0.1,$(hostname -I | awk '{print $1}')'

# Department Info
DEPARTMENT_NAME='$DEPT_NAME'

# Database
DATABASE_URL=postgresql://fdapp:$DB_PASSWORD@localhost:5432/fd_intranet

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Email (configure in admin panel later)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Performance tuned for Raspberry $PI_MODEL
GUNICORN_WORKERS=$RECOMMENDED_WORKERS
GUNICORN_TIMEOUT=120
CACHE_TIMEOUT=3600

# Installation Info
INSTALL_DATE=$(date)
INSTALLED_ON=Raspberry $PI_MODEL
ENVFILE

chown fdapp:fdapp /opt/fd-intranet/app/.env
chmod 600 /opt/fd-intranet/app/.env
print_status "Configuration created"

# Run Django setup
print_info "Step 8/10: Setting up Django..."
cd /opt/fd-intranet/app

sudo -u fdapp /opt/fd-intranet/app/venv/bin/python manage.py makemigrations --noinput >/dev/null 2>&1 || true
sudo -u fdapp /opt/fd-intranet/app/venv/bin/python manage.py migrate --noinput
sudo -u fdapp /opt/fd-intranet/app/venv/bin/python manage.py collectstatic --noinput >/dev/null 2>&1

# Create superuser
sudo -u fdapp /opt/fd-intranet/app/venv/bin/python manage.py shell << PYEOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$ADMIN_EMAIL').exists():
    User.objects.create_superuser('admin', '$ADMIN_EMAIL', '$ADMIN_PASSWORD')
    print("Superuser created")
else:
    print("Superuser already exists")
PYEOF

print_status "Django configured"

# Set up directories
mkdir -p /opt/fd-intranet/{logs,backups,config}
chown -R fdapp:fdapp /opt/fd-intranet

# Create Gunicorn config
cat > /opt/fd-intranet/config/gunicorn_config.py << GUNICORN
# Raspberry $PI_MODEL Optimized Configuration
workers = $RECOMMENDED_WORKERS
worker_class = 'sync'
worker_connections = 50
max_requests = 500
max_requests_jitter = 50
timeout = 120
keepalive = 5
bind = '127.0.0.1:8000'
accesslog = '/opt/fd-intranet/logs/gunicorn_access.log'
errorlog = '/opt/fd-intranet/logs/gunicorn_error.log'
loglevel = 'warning'
proc_name = 'fd_intranet'
daemon = False
pidfile = '/opt/fd-intranet/gunicorn.pid'
user = 'fdapp'
group = 'fdapp'
worker_tmp_dir = '/dev/shm'
GUNICORN

# Configure Supervisor
cat > /etc/supervisor/conf.d/fd-intranet.conf << SUPERVISOR
[program:fd_intranet]
command=/opt/fd-intranet/app/venv/bin/gunicorn core.wsgi:application -c /opt/fd-intranet/config/gunicorn_config.py
directory=/opt/fd-intranet/app
user=fdapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/fd-intranet/logs/gunicorn.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
environment=PATH="/opt/fd-intranet/app/venv/bin"

[program:fd_qcluster]
command=/opt/fd-intranet/app/venv/bin/python manage.py qcluster
directory=/opt/fd-intranet/app
user=fdapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/fd-intranet/logs/qcluster.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=3
environment=PATH="/opt/fd-intranet/app/venv/bin"
SUPERVISOR

supervisorctl reread >/dev/null 2>&1
supervisorctl update >/dev/null 2>&1
sleep 3
print_status "Application services configured"

# Configure Nginx
cat > /etc/nginx/sites-available/fd-intranet << 'NGINX'
upstream fd_intranet {
    server 127.0.0.1:8000 fail_timeout=30s;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    
    client_max_body_size 10M;
    client_body_timeout 30s;
    client_header_timeout 30s;
    keepalive_timeout 30s;
    send_timeout 30s;
    
    location /static/ {
        alias /opt/fd-intranet/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
        gzip_vary on;
    }
    
    location /media/ {
        alias /opt/fd-intranet/app/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://fd_intranet;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering on;
        proxy_buffers 8 16k;
        proxy_buffer_size 16k;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/fd-intranet /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t >/dev/null 2>&1
systemctl restart nginx
print_status "Web server configured"

# Set up firewall
print_info "Step 9/10: Configuring firewall..."
ufw --force enable >/dev/null 2>&1
ufw default deny incoming >/dev/null 2>&1
ufw default allow outgoing >/dev/null 2>&1
ufw allow ssh >/dev/null 2>&1
ufw allow http >/dev/null 2>&1
ufw allow https >/dev/null 2>&1
print_status "Firewall configured"

# Create maintenance scripts
print_info "Step 10/10: Setting up automation..."

# Backup script
cat > /opt/fd-intranet/backup.sh << 'BACKUP'
#!/bin/bash
BACKUP_DIR="/opt/fd-intranet/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump fd_intranet | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
if [ -d "/opt/fd-intranet/app/media" ]; then
    tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /opt/fd-intranet/app media/ 2>/dev/null
fi

# Remove old backups (keep 7 days)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed" >> $BACKUP_DIR/backup.log
BACKUP

chmod +x /opt/fd-intranet/backup.sh
chown fdapp:fdapp /opt/fd-intranet/backup.sh

# Health check script
cat > /opt/fd-intranet/health-check.sh << 'HEALTH'
#!/bin/bash
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)
if [ "$STATUS" != "200" ]; then
    echo "$(date): Health check failed (HTTP $STATUS)" >> /opt/fd-intranet/logs/health.log
    supervisorctl restart fd_intranet >/dev/null 2>&1
fi
HEALTH

chmod +x /opt/fd-intranet/health-check.sh

# Schedule automated tasks
(crontab -u fdapp -l 2>/dev/null; echo "0 2 * * * /opt/fd-intranet/backup.sh") | crontab -u fdapp -
(crontab -u root -l 2>/dev/null; echo "*/5 * * * * /opt/fd-intranet/health-check.sh") | crontab -u root -

print_status "Automation configured"

# Apply Raspberry Pi optimizations
print_info "Applying Raspberry Pi optimizations..."

# Use tmpfs for temporary files (if not already configured)
if ! grep -q "tmpfs /tmp" /etc/fstab; then
    echo "tmpfs /tmp tmpfs defaults,noatime,nosuid,size=512M 0 0" >> /etc/fstab
    echo "tmpfs /var/tmp tmpfs defaults,noatime,nosuid,size=256M 0 0" >> /etc/fstab
    mount -a 2>/dev/null || true
fi

# Reduce GPU memory
BOOT_CONFIG="/boot/firmware/config.txt"
if [ ! -f "$BOOT_CONFIG" ]; then
    BOOT_CONFIG="/boot/config.txt"
fi

if [ -f "$BOOT_CONFIG" ]; then
    if ! grep -q "gpu_mem" "$BOOT_CONFIG"; then
        echo "gpu_mem=16" >> "$BOOT_CONFIG"
    fi
fi

print_status "Optimizations applied"

# Test installation
print_info "Testing installation..."
sleep 5

APP_STATUS=$(supervisorctl status fd_intranet 2>/dev/null | grep -c "RUNNING" || echo "0")
WEB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost 2>/dev/null)

if [ "$APP_STATUS" -eq "1" ]; then
    print_status "Application is running"
else
    print_error "Application failed to start"
    print_warning "Check logs: sudo tail -50 /opt/fd-intranet/logs/gunicorn.log"
fi

if [ "$WEB_STATUS" = "200" ]; then
    print_status "Web server responding"
else
    print_warning "Web server may need a moment to start"
fi

# Save installation info
cat > /root/fd-intranet-install.txt << INSTALL
Fire Department Intranet - Installation Info
=============================================

Installation Date: $(date)
Raspberry Pi Model: $PI_MODEL
Hostname: $DOMAIN
IP Address: $(hostname -I | awk '{print $1}')

Admin Credentials:
  Email: $ADMIN_EMAIL
  Password: [you set this during installation]

Database Credentials:
  User: fdapp
  Password: $DB_PASSWORD
  Database: fd_intranet

Django Secret Key: $SECRET_KEY

Files:
  Application: /opt/fd-intranet/app
  Logs: /opt/fd-intranet/logs
  Backups: /opt/fd-intranet/backups
  Config: /opt/fd-intranet/config

Management:
  sudo supervisorctl status
  sudo supervisorctl restart all
  sudo tail -f /opt/fd-intranet/logs/gunicorn.log

IMPORTANT: Store this file securely and delete after backing up!
INSTALL

chmod 600 /root/fd-intranet-install.txt

# Final summary
clear
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🎉  Installation Complete!  🎉                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF

echo ""
print_status "Fire Department Intranet successfully installed!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 Access your intranet at:"
echo "     http://$DOMAIN"
echo "     http://$(hostname -I | awk '{print $1}')"
echo ""
echo "  👤 Admin login:"
echo "     Email: $ADMIN_EMAIL"
echo "     Password: [the password you set]"
echo ""
echo "  🔧 Quick commands:"
echo "     sudo supervisorctl status        # Check services"
echo "     sudo supervisorctl restart all   # Restart all"
echo "     sudo tail -f /opt/fd-intranet/logs/gunicorn.log"
echo ""
echo "  💾 Backups:"
echo "     Automatic: Daily at 2:00 AM"
echo "     Manual: /opt/fd-intranet/backup.sh"
echo ""
echo "  📊 System info:"
TEMP=$(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 || echo "N/A")
echo "     Temperature: $TEMP"
echo "     Memory: $(free -h | awk 'NR==2{print $3"/"$2}')"
echo "     Disk: $(df -h / | awk 'NR==2{print $3"/"$2}')"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Next steps:"
echo "  1. Visit http://$DOMAIN or http://$(hostname -I | awk '{print $1}')"
echo "  2. Log in with your admin credentials"
echo "  3. Configure email in Django admin"
echo "  4. Add users and start using the system!"
echo ""
print_info "Installation details saved to: /root/fd-intranet-install.txt"
echo ""
print_status "Installation complete! 🚒"
echo ""
