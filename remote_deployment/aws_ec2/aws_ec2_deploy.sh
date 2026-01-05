#!/bin/bash
###############################################################################
# AWS EC2 Deployment Script for Flask App
# Run this after initial setup to deploy your Flask application
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/stock_ticker_generator"
APP_USER="$USER"
APP_NAME="stock_ticker_app"
DOMAIN_NAME=""  # Set your domain name here (or leave empty for IP access)

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Error: app.py not found. Run this script from your project root.${NC}"
    exit 1
fi

echo "🚀 Deploying Flask App to AWS EC2"
echo "=================================="

# Activate virtual environment
echo -e "${GREEN}🐍 Activating virtual environment...${NC}"
source $APP_DIR/venv/bin/activate

# Install Python dependencies
echo -e "${GREEN}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Set up environment variables
echo -e "${GREEN}⚙️  Setting up environment variables...${NC}"

# Get database password (you should set this securely)
read -sp "Enter PostgreSQL password for flask_user: " DB_PASSWORD
echo ""

# Create .env file
cat > $APP_DIR/.env <<EOF
# Database Configuration
DATABASE_URL=postgresql://flask_user:${DB_PASSWORD}@localhost:5432/stocks_db

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# Server Configuration
HOST=0.0.0.0
PORT=5000

# API Keys (set these if needed)
POLYGON_API_KEY=${POLYGON_API_KEY:-}
EOF

echo -e "${GREEN}✅ Environment variables configured${NC}"

# Initialize database
echo -e "${GREEN}🗄️  Initializing database...${NC}"
export DATABASE_URL="postgresql://flask_user:${DB_PASSWORD}@localhost:5432/stocks_db"
python3 -c "from database.database import db_manager; print('Database initialized')" || {
    echo -e "${YELLOW}⚠️  Database initialization - run manually if needed${NC}"
}

# Create Supervisor configuration
echo -e "${GREEN}👷 Creating Supervisor configuration...${NC}"
sudo tee /etc/supervisor/conf.d/${APP_NAME}.conf > /dev/null <<EOF
[program:${APP_NAME}]
command=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 --timeout 120 app:app
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/${APP_NAME}/error.log
stdout_logfile=/var/log/${APP_NAME}/access.log
environment=DATABASE_URL="postgresql://flask_user:${DB_PASSWORD}@localhost:5432/stocks_db"
EOF

# Create log directory
sudo mkdir -p /var/log/${APP_NAME}
sudo chown $APP_USER:$APP_USER /var/log/${APP_NAME}

# Install Gunicorn if not already installed
if ! $APP_DIR/venv/bin/pip show gunicorn > /dev/null 2>&1; then
    echo -e "${GREEN}📦 Installing Gunicorn...${NC}"
    $APP_DIR/venv/bin/pip install gunicorn
fi

# Reload Supervisor
echo -e "${GREEN}🔄 Reloading Supervisor...${NC}"
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ${APP_NAME}

# Configure Nginx
echo -e "${GREEN}🌐 Configuring Nginx...${NC}"

if [ -z "$DOMAIN_NAME" ]; then
    # Use IP address if no domain
    SERVER_NAME="_"
else
    SERVER_NAME="$DOMAIN_NAME"
fi

sudo tee /etc/nginx/sites-available/${APP_NAME} > /dev/null <<EOF
server {
    listen 80;
    server_name ${SERVER_NAME};

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/${APP_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
echo -e "${GREEN}🔄 Restarting Nginx...${NC}"
sudo systemctl restart nginx
sudo systemctl enable nginx

# Configure firewall
echo -e "${GREEN}🔥 Configuring firewall...${NC}"
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw --force enable

# Get public IP
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo -e "${YELLOW}📋 Summary:${NC}"
echo "  - App directory: $APP_DIR"
echo "  - Supervisor: sudo supervisorctl status ${APP_NAME}"
echo "  - Nginx: http://${PUBLIC_IP}"
echo "  - Logs: /var/log/${APP_NAME}/"
echo ""
echo -e "${YELLOW}🔧 Useful commands:${NC}"
echo "  - View app logs: sudo tail -f /var/log/${APP_NAME}/access.log"
echo "  - Restart app: sudo supervisorctl restart ${APP_NAME}"
echo "  - Check status: sudo supervisorctl status ${APP_NAME}"
echo "  - Nginx logs: sudo tail -f /var/log/nginx/error.log"
echo ""
echo -e "${YELLOW}🔒 SSL Setup (if you have a domain):${NC}"
echo "  sudo certbot --nginx -d ${DOMAIN_NAME:-your-domain.com}"
echo ""


