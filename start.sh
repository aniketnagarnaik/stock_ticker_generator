#!/bin/bash
###############################################################################
# Startup Script for Stock Ticker Generator
# This script starts the Flask application with proper environment setup
###############################################################################

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Stock Ticker Generator...${NC}"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    echo -e "${YELLOW}   Creating .env from .env.example...${NC}"
    
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}   Please edit .env file and set your DATABASE_URL${NC}"
        echo -e "${YELLOW}   Then run this script again.${NC}"
        exit 1
    else
        echo -e "${RED}❌ .env.example file not found!${NC}"
        echo -e "${YELLOW}   Please create a .env file with DATABASE_URL${NC}"
        exit 1
    fi
fi

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}❌ DATABASE_URL is not set in .env file!${NC}"
    echo -e "${YELLOW}   Please set DATABASE_URL in .env file${NC}"
    echo -e "${YELLOW}   Example: postgresql://username:password@localhost:5432/stock_ticker_db${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ python3 not found!${NC}"
    echo -e "${YELLOW}   Please install Python 3.11+${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found!${NC}"
    echo -e "${YELLOW}   Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}🐍 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies if needed
echo -e "${GREEN}📦 Checking dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if PostgreSQL is running (optional check)
if command -v pg_isready &> /dev/null; then
    if ! pg_isready -q; then
        echo -e "${YELLOW}⚠️  PostgreSQL may not be running${NC}"
        echo -e "${YELLOW}   Make sure PostgreSQL is started: brew services start postgresql${NC}"
    fi
fi

# Set default PORT if not set
export PORT=${PORT:-5000}

echo -e "${GREEN}✅ Starting Flask application on port $PORT...${NC}"
echo -e "${GREEN}🌐 Access your application at: http://localhost:$PORT${NC}"
echo ""

# Start Flask app
python3 app.py
