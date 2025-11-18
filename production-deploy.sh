#!/bin/bash

# Production Deployment Script for ATS Resume Checker
# Run with: sudo ./production-deploy.sh

set -e  # Exit on any error

echo "🚀 Starting ATS Resume Checker Production Deployment..."

# Configuration
APP_NAME="ats-resume-checker"
APP_DIR="/opt/$APP_NAME"
APP_USER="www-data"
PYTHON_VERSION="3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Run as regular user with sudo privileges."
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    postgresql-client \
    redis-tools \
    nginx \
    supervisor \
    git \
    curl \
    build-essential \
    libpq-dev \
    certbot \
    python3-certbot-nginx

# Create application directory
print_status "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Copy application files
print_status "Copying application files..."
cp -r . $APP_DIR/
cd $APP_DIR

# Create virtual environment
print_status "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
print_status "Creating application directories..."
mkdir -p logs uploads exports instance backups
sudo chown -R $APP_USER:$APP_USER $APP_DIR

# Set up environment variables
print_status "Configuring environment variables..."
if [ ! -f .env ]; then
    print_error ".env file not found! Please create it first."
    exit 1
fi

# Generate secret key if needed
if grep -q "CHANGE_THIS_SECRET_KEY" .env; then
    print_warning "Generating new SECRET_KEY..."
    NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/CHANGE_THIS_SECRET_KEY_FOR_PRODUCTION_USE_RANDOM_64_CHAR_STRING/$NEW_SECRET/" .env
fi

# Initialize database
print_status "Initializing database..."
python init_db.py

# Set up Nginx
print_status "Configuring Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/$APP_NAME
sudo ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Set up systemd service
print_status "Setting up systemd service..."
sudo cp $APP_NAME.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME

# Set up SSL certificate (Let's Encrypt)
print_warning "Setting up SSL certificate..."
echo "Please enter your domain name (e.g., example.com):"
read DOMAIN_NAME

if [ ! -z "$DOMAIN_NAME" ]; then
    # Update Nginx config with actual domain
    sudo sed -i "s/your-domain.com/$DOMAIN_NAME/g" /etc/nginx/sites-available/$APP_NAME
    
    # Get SSL certificate
    sudo certbot --nginx -d $DOMAIN_NAME -d www.$DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME
else
    print_warning "Skipping SSL setup. Configure manually later."
fi

# Start services
print_status "Starting services..."
sudo systemctl start $APP_NAME
sudo systemctl reload nginx

# Set up log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/$APP_NAME > /dev/null <<EOF
$APP_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $APP_USER $APP_USER
    postrotate
        systemctl reload $APP_NAME
    endscript
}
EOF

# Set up backup cron job
print_status "Setting up backup cron job..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $APP_DIR && python backup_manager.py") | crontab -

# Verify deployment
print_status "Verifying deployment..."
sleep 5

if systemctl is-active --quiet $APP_NAME; then
    print_status "✅ Application service is running"
else
    print_error "❌ Application service failed to start"
    sudo systemctl status $APP_NAME
fi

if systemctl is-active --quiet nginx; then
    print_status "✅ Nginx is running"
else
    print_error "❌ Nginx failed to start"
    sudo systemctl status nginx
fi

# Test application
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    print_status "✅ Application health check passed"
else
    print_warning "⚠️  Application health check failed - check logs"
fi

echo
print_status "🎉 Deployment completed successfully!"
echo
echo "Next steps:"
echo "1. Configure your DNS to point to this server"
echo "2. Update .env with your production database URL"
echo "3. Set up monitoring and alerting"
echo "4. Configure backup storage (AWS S3, etc.)"
echo
echo "Useful commands:"
echo "  sudo systemctl status $APP_NAME     # Check app status"
echo "  sudo systemctl restart $APP_NAME    # Restart app"
echo "  sudo journalctl -u $APP_NAME -f     # View app logs"
echo "  sudo nginx -t && sudo systemctl reload nginx  # Reload Nginx"
echo
echo "Application should be available at: https://$DOMAIN_NAME"