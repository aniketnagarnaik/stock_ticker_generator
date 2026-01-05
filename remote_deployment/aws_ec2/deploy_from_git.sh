#!/bin/bash
###############################################################################
# Git-Based Deployment Script
# Pulls latest code from Git and redeploys the app
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/stock_ticker_generator"
APP_NAME="stock_ticker_app"
BRANCH="main"  # Change to 'master' if your default branch is master

echo "🚀 Deploying from Git..."
echo "========================="

# Navigate to app directory
cd $APP_DIR

# Activate virtual environment
echo -e "${GREEN}🐍 Activating virtual environment...${NC}"
source venv/bin/activate

# Pull latest code
echo -e "${GREEN}📥 Pulling latest code from Git...${NC}"
git fetch origin
git reset --hard origin/$BRANCH
git clean -fd

# Install/update dependencies
echo -e "${GREEN}📦 Installing/updating dependencies...${NC}"
pip install -r requirements.txt --upgrade

# Load environment variables
if [ -f .env ]; then
    echo -e "${GREEN}⚙️  Loading environment variables...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run database migrations (if needed)
echo -e "${GREEN}🗄️  Checking database...${NC}"
python3 -c "from database.database import db_manager; print('Database ready')" || {
    echo -e "${YELLOW}⚠️  Database check - continuing anyway${NC}"
}

# Restart application
echo -e "${GREEN}🔄 Restarting application...${NC}"
sudo supervisorctl restart $APP_NAME

# Wait a moment for app to start
sleep 3

# Check if app is running
if sudo supervisorctl status $APP_NAME | grep -q "RUNNING"; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    echo ""
    echo -e "${YELLOW}📋 App Status:${NC}"
    sudo supervisorctl status $APP_NAME
else
    echo -e "${RED}❌ Deployment failed - check logs${NC}"
    echo -e "${YELLOW}View logs: sudo tail -f /var/log/${APP_NAME}/error.log${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Your app is now running the latest code!${NC}"


