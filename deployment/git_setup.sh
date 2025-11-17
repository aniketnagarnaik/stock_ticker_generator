#!/bin/bash
###############################################################################
# Initial Git-Based Setup for AWS EC2
# Clones your repository and sets up the environment
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration - CHANGE THESE!
GIT_REPO_URL=""  # Your Git repository URL (e.g., https://github.com/username/repo.git)
GIT_BRANCH="main"  # Your default branch (main or master)
APP_DIR="/opt/stock_ticker_generator"

echo "🚀 Git-Based Setup for Flask + PostgreSQL App"
echo "=============================================="

# Check if Git repo URL is set
if [ -z "$GIT_REPO_URL" ]; then
    echo -e "${RED}❌ Error: GIT_REPO_URL is not set!${NC}"
    echo -e "${YELLOW}Edit this script and set GIT_REPO_URL to your repository URL${NC}"
    exit 1
fi

# Update system
echo -e "${GREEN}📦 Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

# Install essential packages
echo -e "${GREEN}📦 Installing essential packages...${NC}"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    supervisor \
    git \
    curl \
    wget \
    build-essential \
    libpq-dev \
    python3-dev \
    certbot \
    python3-certbot-nginx

# Install PostgreSQL
echo -e "${GREEN}🐘 Setting up PostgreSQL...${NC}"
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create PostgreSQL database and user
echo -e "${GREEN}🐘 Creating PostgreSQL database and user...${NC}"
read -sp "Enter PostgreSQL password for flask_user: " DB_PASSWORD
echo ""

sudo -u postgres psql <<EOF
-- Create database
CREATE DATABASE stocks_db;

-- Create user
CREATE USER flask_user WITH PASSWORD '${DB_PASSWORD}';

-- Grant privileges
ALTER ROLE flask_user SET client_encoding TO 'utf8';
ALTER ROLE flask_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE flask_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE stocks_db TO flask_user;

-- Connect to database and grant schema privileges
\c stocks_db
GRANT ALL ON SCHEMA public TO flask_user;

\q
EOF

# Create application directory
echo -e "${GREEN}📁 Creating application directory...${NC}"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone repository
echo -e "${GREEN}📥 Cloning repository from Git...${NC}"
cd /opt
if [ -d "$APP_DIR/.git" ]; then
    echo -e "${YELLOW}Repository already exists, pulling latest...${NC}"
    cd $APP_DIR
    git pull origin $GIT_BRANCH
else
    git clone $GIT_REPO_URL $APP_DIR
    cd $APP_DIR
    git checkout $GIT_BRANCH
fi

# Create virtual environment
echo -e "${GREEN}🐍 Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo -e "${GREEN}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Create .env file
echo -e "${GREEN}⚙️  Creating .env file...${NC}"
if [ ! -f .env ]; then
    cat > .env <<ENVEOF
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
POLYGON_API_KEY=
ENVEOF
    echo -e "${GREEN}✅ .env file created${NC}"
    echo -e "${YELLOW}⚠️  Edit .env file to add your API keys if needed${NC}"
else
    echo -e "${YELLOW}.env file already exists, skipping...${NC}"
fi

echo -e "${GREEN}✅ Git-based setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file if needed: nano $APP_DIR/.env"
echo "2. Run deployment script: ./deployment/aws_ec2_deploy.sh"
echo ""

