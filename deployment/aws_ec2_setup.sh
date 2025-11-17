#!/bin/bash
###############################################################################
# AWS EC2 Setup Script for Flask + PostgreSQL App
# This script sets up everything on a fresh Ubuntu 24.04 EC2 instance
# Compatible with: Ubuntu 24.04 LTS (Noble)
###############################################################################

set -e  # Exit on any error

echo "🚀 Starting AWS EC2 Setup for Flask + PostgreSQL App"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
sudo -u postgres psql <<EOF
-- Create database
CREATE DATABASE stocks_db;

-- Create user
CREATE USER flask_user WITH PASSWORD 'CHANGE_THIS_PASSWORD';

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

echo -e "${YELLOW}⚠️  IMPORTANT: Change the PostgreSQL password above!${NC}"
echo -e "${YELLOW}   Edit this script and replace 'CHANGE_THIS_PASSWORD'${NC}"

# Create application directory
echo -e "${GREEN}📁 Creating application directory...${NC}"
APP_DIR="/opt/stock_ticker_generator"
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Create virtual environment
echo -e "${GREEN}🐍 Creating Python virtual environment...${NC}"
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

echo -e "${GREEN}✅ Basic setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Clone your repository: cd $APP_DIR && git clone <your-repo-url> ."
echo "2. Install dependencies: source venv/bin/activate && pip install -r requirements.txt"
echo "3. Set up environment variables (DATABASE_URL, etc.)"
echo "4. Run database migrations"
echo "5. Configure Nginx and Supervisor"
echo ""
echo -e "${GREEN}Run the deployment script next!${NC}"

