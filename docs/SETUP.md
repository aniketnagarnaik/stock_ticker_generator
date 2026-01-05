# 🚀 Setup Guide

Complete setup instructions for the Stock Ticker Generator application.

## 📋 Prerequisites

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **PostgreSQL 14+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **Modern web browser** - Chrome, Firefox, Safari, or Edge

### Installing PostgreSQL

#### macOS (using Homebrew)
```bash
brew install postgresql@14
brew services start postgresql@14
```

#### Windows
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

## 🔧 Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/aniketnagarnaik/stock_ticker_generator.git
cd stock_ticker_generator
```

### 2. Create PostgreSQL Database

#### Using `createdb` command (recommended)
```bash
# Create database (replace 'your_username' with your PostgreSQL username)
createdb -U your_username stock_ticker_db
```

#### Using `psql` command line
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE stock_ticker_db;

# Exit psql
\q
```

#### Using pgAdmin (GUI)
1. Open pgAdmin
2. Connect to your PostgreSQL server
3. Right-click on "Databases" → "Create" → "Database"
4. Name: `stock_ticker_db`
5. Click "Save"

### 3. Create Environment Configuration File

Create a `.env` file in the project root:

```bash
# On Unix/Mac:
touch .env

# On Windows:
type nul > .env
```

Edit the `.env` file and add your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/stock_ticker_db

# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development

# Server Configuration
PORT=5000

# API Keys (optional)
# POLYGON_API_KEY=your_polygon_api_key_here
```

**Important Notes:**
- Replace `username` with your PostgreSQL username (often `postgres` on Windows/Linux, or your system username on macOS)
- Replace `password` with your PostgreSQL password
- Replace `stock_ticker_db` if you used a different database name
- Keep `.env` file secure - it contains sensitive information
- The `.env` file is already in `.gitignore` and won't be committed to Git

### 4. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Unix/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 5. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Verify Database Connection

```bash
# Test database connection
python3 -c "from database.database import db_manager; print('✅ Database connection successful')"
```

If you see "✅ Database connection successful", you're ready to go!

## 🚀 Running the Application

### Option A: Using Startup Script (Recommended)

The startup script automatically handles environment setup:

#### On Unix/Mac:
```bash
./start.sh
```

#### On Windows:
```bash
start.bat
```

The script will:
- Check if `.env` file exists
- Verify database connection
- Activate virtual environment
- Install dependencies if needed
- Start the Flask server

### Option B: Run Directly

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
python3 app.py
```

### 7. Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

## 🔍 Troubleshooting

### Database Connection Errors

**Error: `connection to server at "localhost" (::1), port 5432 failed`**

- **Solution**: Make sure PostgreSQL is running
  ```bash
  # macOS (Homebrew)
  brew services start postgresql@14
  
  # Linux
  sudo systemctl start postgresql
  
  # Windows
  # Start PostgreSQL service from Services panel
  ```

**Error: `database "stock_ticker_db" does not exist`**

- **Solution**: Create the database (see Step 2 above)

**Error: `password authentication failed`**

- **Solution**: Check your username and password in `.env` file
- Verify PostgreSQL user credentials

### Python/Dependencies Errors

**Error: `python3: command not found`**

- **Solution**: Install Python 3.11+ or use `python` instead of `python3`

**Error: `pip: command not found`**

- **Solution**: Install pip or use `python3 -m pip` instead

**Error: `ModuleNotFoundError: No module named 'dotenv'`**

- **Solution**: Install dependencies: `pip install -r requirements.txt`

### Port Already in Use

**Error: `Address already in use`**

- **Solution**: Kill the process using port 5000:
  ```bash
  # Unix/Mac
  lsof -ti:5000 | xargs kill -9
  
  # Windows
  netstat -ano | findstr :5000
  taskkill /PID <PID> /F
  ```

Or change the PORT in your `.env` file to a different port (e.g., 5001).

## 📝 Next Steps

1. **Populate Database**: The database tables are created automatically when you first run the app
2. **Load Stock Data**: Use the refresh endpoint or UI to load stock data
3. **Explore Features**: Check out the filtering and analysis features
4. **Read Documentation**: See `docs/DEVELOPER_GUIDE.md` for code structure

## 🆘 Getting Help

- Check the [README.md](../README.md) for quick reference
- Review [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for code structure
- Open an issue on GitHub if you encounter bugs

## ✅ Setup Checklist

- [ ] Python 3.11+ installed
- [ ] PostgreSQL installed and running
- [ ] Database `stock_ticker_db` created
- [ ] `.env` file created with DATABASE_URL
- [ ] Virtual environment created (recommended)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database connection verified
- [ ] Application running on http://localhost:5000
