# 🚀 Production Deployment Guide

## Fire Department Intranet - Complete Deployment Instructions

This guide covers deploying the fire department intranet to a production server with full security, backups, and monitoring.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Database Configuration](#database-configuration)
4. [Application Deployment](#application-deployment)
5. [Web Server Configuration](#web-server-configuration)
6. [SSL/TLS Setup](#ssltls-setup)
7. [Background Tasks](#background-tasks)
8. [Security Hardening](#security-hardening)
9. [Backup Configuration](#backup-configuration)
10. [Monitoring Setup](#monitoring-setup)
11. [Maintenance Procedures](#maintenance-procedures)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### **Minimum Server Requirements:**

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 50 GB | 100 GB SSD |
| Bandwidth | 10 Mbps | 100 Mbps |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

### **Required Software:**
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Nginx 1.18+
- Git
- Supervisor (for process management)

### **Domain & DNS:**
- Registered domain name
- DNS A record pointing to server IP
- SSL certificate (Let's Encrypt or commercial)

---

## Server Setup

### **1. Initial Server Configuration**

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    supervisor \
    git \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    vim

# Set timezone (adjust as needed)
sudo timedatectl set-timezone America/New_York

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

### **2. Create Application User**

```bash
# Create dedicated user for application
sudo adduser --system --group --home /opt/fd-intranet fdapp

# Add current user to fdapp group (for management)
sudo usermod -aG fdapp $USER

# Set up directory structure
sudo mkdir -p /opt/fd-intranet
sudo chown fdapp:fdapp /opt/fd-intranet
sudo chmod 750 /opt/fd-intranet
```

---

## Database Configuration

### **1. PostgreSQL Setup**

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL console:
CREATE DATABASE fd_intranet;
CREATE USER fdapp WITH PASSWORD 'STRONG_PASSWORD_HERE';
ALTER ROLE fdapp SET client_encoding TO 'utf8';
ALTER ROLE fdapp SET default_transaction_isolation TO 'read committed';
ALTER ROLE fdapp SET timezone TO 'America/New_York';
GRANT ALL PRIVILEGES ON DATABASE fd_intranet TO fdapp;

# Enable SSL (recommended)
ALTER DATABASE fd_intranet SET ssl TO on;

# Exit PostgreSQL
\q
```

### **2. PostgreSQL Optimization**

Edit `/etc/postgresql/14/main/postgresql.conf`:

```conf
# Memory Configuration
shared_buffers = 1GB                    # 25% of system RAM
effective_cache_size = 3GB              # 75% of system RAM
maintenance_work_mem = 256MB
work_mem = 16MB

# Connection Configuration
max_connections = 100

# Write Performance
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query Planning
random_page_cost = 1.1                  # For SSD
effective_io_concurrency = 200          # For SSD

# Logging
log_destination = 'stderr'
logging_collector = on
log_directory = '/var/log/postgresql'
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_min_duration_statement = 1000       # Log queries > 1 second
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### **3. Database Backups**

Create backup script `/opt/fd-intranet/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/fd-intranet/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Perform backup
pg_dump -U fdapp -h localhost fd_intranet | \
    gzip > $BACKUP_DIR/fd_intranet_$DATE.sql.gz

# Remove old backups
find $BACKUP_DIR -name "fd_intranet_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Log backup
echo "$(date): Database backup completed - fd_intranet_$DATE.sql.gz" >> $BACKUP_DIR/backup.log
```

Make executable and schedule:

```bash
sudo chmod +x /opt/fd-intranet/backup_db.sh
sudo chown fdapp:fdapp /opt/fd-intranet/backup_db.sh

# Add to crontab for fdapp user
sudo -u fdapp crontab -e
# Add line:
0 2 * * * /opt/fd-intranet/backup_db.sh
```

---

## Application Deployment

### **1. Clone Repository**

```bash
# Switch to fdapp user
sudo -u fdapp -i

# Navigate to home directory
cd /opt/fd-intranet

# Clone repository
git clone https://github.com/your-org/fd-intranet.git app
cd app

# Or if deploying from local:
# scp -r fd-intranet/ user@server:/opt/fd-intranet/app
```

### **2. Python Virtual Environment**

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Install production dependencies
pip install gunicorn psycopg2-binary
```

### **3. Environment Configuration**

Create `/opt/fd-intranet/app/.env`:

```bash
# CRITICAL: Generate strong secret key
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY='YOUR_GENERATED_SECRET_KEY_HERE_50_CHARS_MIN'

# Environment
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://fdapp:STRONG_PASSWORD_HERE@localhost:5432/fd_intranet

# Email Configuration (adjust for your provider)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=alerts@yourfiredept.org
EMAIL_HOST_PASSWORD=YOUR_APP_PASSWORD_HERE
DEFAULT_FROM_EMAIL=noreply@yourfiredept.org

# AWS S3 (if using)
USE_S3=True
AWS_ACCESS_KEY_ID=YOUR_AWS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET
AWS_STORAGE_BUCKET_NAME=fd-intranet-docs
AWS_S3_REGION_NAME=us-east-1

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Geographic Security
GEO_SECURITY_ENABLED=True
TIME_ZONE=America/New_York

# Integration APIs (add as needed)
TARGET_SOLUTIONS_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MS_CLIENT_ID=
MS_CLIENT_SECRET=
NOCODB_API_TOKEN=
```

**CRITICAL:** Set proper permissions:

```bash
chmod 600 /opt/fd-intranet/app/.env
chown fdapp:fdapp /opt/fd-intranet/app/.env
```

### **4. Django Application Setup**

```bash
# Activate virtual environment
cd /opt/fd-intranet/app
source venv/bin/activate

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run setup system
python manage.py setup_system

# Test that it works
python manage.py check --deploy
```

---

## Web Server Configuration

### **1. Gunicorn Configuration**

Create `/opt/fd-intranet/app/gunicorn_config.py`:

```python
"""Gunicorn configuration for production"""
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 60
keepalive = 5

# Process naming
proc_name = 'fd-intranet'

# Logging
accesslog = '/opt/fd-intranet/logs/gunicorn_access.log'
errorlog = '/opt/fd-intranet/logs/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Server mechanics
daemon = False
pidfile = '/opt/fd-intranet/gunicorn.pid'
user = 'fdapp'
group = 'fdapp'
umask = 0o007

# SSL (if terminating SSL at Gunicorn instead of Nginx)
# keyfile = '/path/to/key.pem'
# certfile = '/path/to/cert.pem'
```

Create log directory:

```bash
sudo mkdir -p /opt/fd-intranet/logs
sudo chown fdapp:fdapp /opt/fd-intranet/logs
sudo chmod 750 /opt/fd-intranet/logs
```

### **2. Supervisor Configuration**

Create `/etc/supervisor/conf.d/fd-intranet.conf`:

```ini
[program:fd-intranet]
command=/opt/fd-intranet/app/venv/bin/gunicorn core.wsgi:application -c /opt/fd-intranet/app/gunicorn_config.py
directory=/opt/fd-intranet/app
user=fdapp
group=fdapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/fd-intranet/logs/gunicorn_supervisor.log
stderr_logfile=/opt/fd-intranet/logs/gunicorn_supervisor_error.log
environment=PATH="/opt/fd-intranet/app/venv/bin"

[program:fd-intranet-worker]
command=/opt/fd-intranet/app/venv/bin/python manage.py qcluster
directory=/opt/fd-intranet/app
user=fdapp
group=fdapp
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/opt/fd-intranet/logs/qcluster.log
stderr_logfile=/opt/fd-intranet/logs/qcluster_error.log
environment=PATH="/opt/fd-intranet/app/venv/bin"
```

Start services:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fd-intranet
sudo supervisorctl start fd-intranet-worker

# Check status
sudo supervisorctl status
```

### **3. Nginx Configuration**

Create `/etc/nginx/sites-available/fd-intranet`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

# Upstream to Gunicorn
upstream fd_intranet {
    server 127.0.0.1:8000 fail_timeout=0;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Allow Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' data: https://cdn.jsdelivr.net;" always;
    
    # Client body size (for file uploads)
    client_max_body_size 50M;
    
    # Logging
    access_log /var/log/nginx/fd-intranet-access.log;
    error_log /var/log/nginx/fd-intranet-error.log warn;
    
    # Static files
    location /static/ {
        alias /opt/fd-intranet/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /opt/fd-intranet/app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Login rate limiting
    location /accounts/login/ {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://fd_intranet;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }
    
    # API rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://fd_intranet;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }
    
    # All other requests
    location / {
        proxy_pass http://fd_intranet;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_buffering off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/fd-intranet /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/TLS Setup

### **Using Let's Encrypt (Free)**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test renewal
sudo certbot renew --dry-run

# Auto-renewal is configured via cron/systemd timer
```

### **Using Commercial Certificate**

```bash
# Copy certificate files to server
sudo cp yourdomain.com.crt /etc/ssl/certs/
sudo cp yourdomain.com.key /etc/ssl/private/
sudo cp ca-bundle.crt /etc/ssl/certs/

# Set permissions
sudo chmod 644 /etc/ssl/certs/yourdomain.com.crt
sudo chmod 600 /etc/ssl/private/yourdomain.com.key
sudo chown root:root /etc/ssl/certs/yourdomain.com.crt
sudo chown root:root /etc/ssl/private/yourdomain.com.key

# Update Nginx configuration with paths
# Then restart Nginx
sudo systemctl restart nginx
```

---

## Background Tasks

### **Django-Q Configuration**

Already configured in Supervisor above. Verify it's running:

```bash
sudo supervisorctl status fd-intranet-worker
```

### **Scheduled Tasks**

Tasks are configured in Django admin under Django Q > Scheduled tasks.

**Important tasks to schedule:**

```python
# Training expiration alerts - Daily at 07:00
Name: Training Expiration Alerts
Func: training.services.send_training_alerts
Schedule Type: Daily
Time: 07:00

# Compliance checks - Daily at 06:00
Name: HIPAA Compliance Check
Func: compliance.hipaa_compliance.run_hipaa_compliance_checks
Schedule Type: Daily
Time: 06:00

# Weekly audit digest - Monday at 08:00
Name: Weekly Audit Digest
Func: core.weekly_digest.send_weekly_digest
Schedule Type: Weekly
Day: Monday
Time: 08:00

# Target Solutions sync - Daily at 02:00
Name: Target Solutions Sync
Func: training.services.sync_from_target_solutions
Schedule Type: Daily
Time: 02:00

# NocoDB sync - Daily at 03:00
Name: NocoDB Sync
Func: integrations.nocodb_client.sync_all_data
Schedule Type: Daily
Time: 03:00
```

---

## Security Hardening

### **1. Fail2Ban Configuration**

Create `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
destemail = security@yourfiredept.org
sendername = Fail2Ban
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/fd-intranet-error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/fd-intranet-error.log
maxretry = 10

[nginx-botsearch]
enabled = true
port = http,https
logpath = /var/log/nginx/fd-intranet-access.log
maxretry = 2
```

Start Fail2Ban:

```bash
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
sudo fail2ban-client status
```

### **2. System Updates**

```bash
# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

Edit `/etc/apt/apt.conf.d/50unattended-upgrades`:

```conf
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
Unattended-Upgrade::Mail "admin@yourfiredept.org";
```

### **3. SSH Hardening**

Edit `/etc/ssh/sshd_config`:

```conf
# Change default port (optional but recommended)
Port 2222

# Disable root login
PermitRootLogin no

# Use SSH keys only
PasswordAuthentication no
PubkeyAuthentication yes

# Limit users
AllowUsers yourusername

# Disable empty passwords
PermitEmptyPasswords no

# Timeout settings
ClientAliveInterval 300
ClientAliveCountMax 2
```

Restart SSH:

```bash
sudo systemctl restart sshd
```

### **4. File Permissions**

```bash
# Application files
sudo chown -R fdapp:fdapp /opt/fd-intranet
sudo find /opt/fd-intranet/app -type d -exec chmod 750 {} \;
sudo find /opt/fd-intranet/app -type f -exec chmod 640 {} \;

# Make manage.py executable
sudo chmod 750 /opt/fd-intranet/app/manage.py

# Secure .env file
sudo chmod 600 /opt/fd-intranet/app/.env

# Media/upload directories
sudo chmod 770 /opt/fd-intranet/app/media
```

---

## Backup Configuration

### **1. Application Backup Script**

Create `/opt/fd-intranet/backup_app.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/fd-intranet/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p $BACKUP_DIR

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz \
    -C /opt/fd-intranet/app media/

# Backup configuration
cp /opt/fd-intranet/app/.env $BACKUP_DIR/env_$DATE

# Remove old backups
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "env_*" -mtime +$RETENTION_DAYS -delete

echo "$(date): Application backup completed" >> $BACKUP_DIR/backup.log
```

### **2. Offsite Backup**

Configure S3 backup:

```bash
# Install AWS CLI
sudo apt install awscli

# Configure AWS credentials
sudo -u fdapp aws configure

# Create S3 sync script
cat > /opt/fd-intranet/backup_to_s3.sh << 'EOF'
#!/bin/bash
aws s3 sync /opt/fd-intranet/backups/ \
    s3://your-backup-bucket/fd-intranet-backups/ \
    --storage-class GLACIER \
    --exclude "*" \
    --include "*.sql.gz" \
    --include "*.tar.gz"
EOF

sudo chmod +x /opt/fd-intranet/backup_to_s3.sh

# Schedule in crontab
sudo -u fdapp crontab -e
# Add:
0 4 * * * /opt/fd-intranet/backup_to_s3.sh
```

---

## Monitoring Setup

### **1. System Monitoring**

Install monitoring tools:

```bash
sudo apt install htop iotop nethogs
```

### **2. Log Monitoring**

Create log rotation config `/etc/logrotate.d/fd-intranet`:

```conf
/opt/fd-intranet/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 fdapp fdapp
    sharedscripts
    postrotate
        supervisorctl restart fd-intranet > /dev/null
    endscript
}
```

### **3. Health Check Script**

Create `/opt/fd-intranet/health_check.sh`:

```bash
#!/bin/bash
ALERT_EMAIL="admin@yourfiredept.org"

# Check if web server is responding
if ! curl -s -o /dev/null -w "%{http_code}" https://yourdomain.com | grep -q "200\|302"; then
    echo "Web server not responding" | mail -s "FD Intranet DOWN" $ALERT_EMAIL
fi

# Check database
if ! sudo -u fdapp psql -h localhost -U fdapp -d fd_intranet -c "SELECT 1" > /dev/null 2>&1; then
    echo "Database not responding" | mail -s "FD Intranet Database DOWN" $ALERT_EMAIL
fi

# Check disk space
DISK_USAGE=$(df -h /opt/fd-intranet | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "Disk usage at ${DISK_USAGE}%" | mail -s "FD Intranet Disk Space Warning" $ALERT_EMAIL
fi
```

Schedule health checks:

```bash
sudo crontab -e
# Add:
*/5 * * * * /opt/fd-intranet/health_check.sh
```

---

## Maintenance Procedures

### **Daily Tasks**

```bash
# Check logs for errors
sudo tail -f /opt/fd-intranet/logs/gunicorn_error.log

# Check Supervisor status
sudo supervisorctl status

# Monitor system resources
htop
```

### **Weekly Tasks**

```bash
# Review backup logs
cat /opt/fd-intranet/backups/backup.log

# Check disk space
df -h

# Review security logs
sudo fail2ban-client status
```

### **Monthly Tasks**

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Review and rotate logs
sudo logrotate -f /etc/logrotate.d/fd-intranet

# Test database restore
# (perform in non-production environment)

# Review user accounts and permissions
sudo -u fdapp python /opt/fd-intranet/app/manage.py shell
>>> from django.contrib.auth.models import User
>>> User.objects.filter(is_active=True).count()
```

### **Deploying Updates**

```bash
# 1. Backup current version
cd /opt/fd-intranet
sudo -u fdapp tar -czf backup_$(date +%Y%m%d).tar.gz app/

# 2. Pull latest code
cd /opt/fd-intranet/app
sudo -u fdapp git pull origin main

# 3. Activate virtual environment
sudo -u fdapp bash
source venv/bin/activate

# 4. Update dependencies
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Collect static files
python manage.py collectstatic --noinput

# 7. Restart services
exit
sudo supervisorctl restart fd-intranet
sudo supervisorctl restart fd-intranet-worker

# 8. Check logs
sudo tail -f /opt/fd-intranet/logs/gunicorn_supervisor.log
```

---

## Troubleshooting

### **Application Won't Start**

```bash
# Check Supervisor logs
sudo tail -100 /opt/fd-intranet/logs/gunicorn_supervisor_error.log

# Check Django for errors
cd /opt/fd-intranet/app
sudo -u fdapp bash -c "source venv/bin/activate && python manage.py check"

# Verify .env file
sudo -u fdapp cat /opt/fd-intranet/app/.env

# Check file permissions
ls -la /opt/fd-intranet/app/
```

### **Database Connection Issues**

```bash
# Test database connection
sudo -u fdapp psql -h localhost -U fdapp -d fd_intranet

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### **Static Files Not Loading**

```bash
# Verify static files collected
ls -la /opt/fd-intranet/app/staticfiles/

# Check Nginx configuration
sudo nginx -t

# Verify Nginx can read static files
sudo -u www-data ls /opt/fd-intranet/app/staticfiles/
```

### **SSL Certificate Issues**

```bash
# Test SSL configuration
sudo nginx -t

# Check certificate expiry
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --force-renewal
```

### **Performance Issues**

```bash
# Check system resources
htop

# Check slow queries
sudo -u postgres psql -d fd_intranet -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;"

# Check Gunicorn worker count
ps aux | grep gunicorn | wc -l

# Monitor real-time logs
sudo tail -f /opt/fd-intranet/logs/gunicorn_access.log
```

---

## Post-Deployment Checklist

- [ ] Server secured (firewall, SSH, fail2ban)
- [ ] PostgreSQL installed and optimized
- [ ] Redis installed and running
- [ ] Application deployed
- [ ] Environment variables configured
- [ ] Database migrated
- [ ] Superuser created
- [ ] Groups and roles configured
- [ ] Static files collected
- [ ] Gunicorn running via Supervisor
- [ ] Background worker running
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Scheduled tasks configured
- [ ] Backups automated
- [ ] Monitoring configured
- [ ] Health checks running
- [ ] DNS pointing to server
- [ ] Email notifications working
- [ ] Test login successful
- [ ] All features tested
- [ ] Documentation updated
- [ ] Team trained

---

## Support & Resources
