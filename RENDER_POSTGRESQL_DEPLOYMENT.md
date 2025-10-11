# Render + PostgreSQL + GitHub Actions Deployment Guide

## 🎯 **New Architecture**
```
GitHub Actions (Free) → Triggers → Render App (Free) → Render PostgreSQL (Free)
     ↓
Daily at 4:45 PM PT → HTTP endpoint → Refresh data → Store in PostgreSQL
```

## ✅ **What's Changed**
- ✅ **Removed SQLite** - No more local database files
- ✅ **Added PostgreSQL support** - Uses Render's managed database
- ✅ **Added GitHub Actions** - Automated daily refresh
- ✅ **Simplified architecture** - No background workers needed
- ✅ **Completely free** - All services use free tiers

## 🚀 **Deployment Steps**

### **1. Deploy to Render**

#### **A. Create Render PostgreSQL Database**
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Choose **"Free"** plan
4. Name: `stock-ticker-db`
5. Click **"Create Database"**
6. Copy the **DATABASE_URL** (you'll need this)

#### **B. Create Render Web Service**
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `stock-ticker-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app_new.py`
4. Add Environment Variables:
   - `DATABASE_URL`: (paste from step A)
   - `LOG_LEVEL`: `INFO`

#### **C. Deploy**
1. Click **"Create Web Service"**
2. Wait for deployment to complete
3. Note your app URL (e.g., `https://stock-ticker-app.onrender.com`)

### **2. Setup GitHub Actions**

#### **A. Add Repository Secret**
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**
4. Name: `RENDER_APP_URL`
5. Value: Your Render app URL (e.g., `https://stock-ticker-app.onrender.com`)
6. Click **"Add secret"**

#### **B. Enable GitHub Actions**
1. Push your code to GitHub
2. Go to **Actions** tab in your repository
3. You should see the **"Daily Stock Data Refresh"** workflow
4. Click on it and click **"Enable workflow"**

### **3. Initial Data Load**

#### **Manual Refresh (First Time)**
1. Go to your Render app URL
2. Visit: `https://your-app.onrender.com/api/refresh`
3. This will trigger the first data load
4. Wait for completion (5-10 minutes)

## 🎯 **How It Works**

### **Daily Schedule:**
- **4:45 PM PT daily** → GitHub Actions triggers
- **HTTP POST** → Your Render app `/api/refresh` endpoint
- **Data refresh** → Fetches 503 stocks from Yahoo Finance
- **Store in PostgreSQL** → Persistent database storage
- **Web app serves** → Instant data from database

### **Benefits:**
- ✅ **No 7-minute load times** - data served from PostgreSQL
- ✅ **No cold start issues** - data is always fresh
- ✅ **Completely free** - all services use free tiers
- ✅ **Reliable** - GitHub Actions is very stable
- ✅ **Persistent** - PostgreSQL never loses data

## 🔧 **Testing**

### **Test Refresh Endpoint:**
```bash
# Manual refresh
curl -X POST https://your-app.onrender.com/api/refresh

# Check status
curl https://your-app.onrender.com/api/status

# Health check
curl https://your-app.onrender.com/api/health
```

### **Test GitHub Actions:**
1. Go to **Actions** tab in GitHub
2. Click **"Daily Stock Data Refresh"**
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch the logs to see it trigger your app

## 📊 **Expected Performance**

| Metric | Before | After |
|--------|--------|-------|
| **First Load** | 7 minutes | < 1 second |
| **Cold Start** | 1 minute | 10-30 seconds |
| **Data Freshness** | Stale | Daily refresh |
| **Cost** | Free | Free |
| **Reliability** | Low | High |

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **1. Database Connection Error**
- Check `DATABASE_URL` environment variable
- Ensure PostgreSQL service is running
- Verify database credentials

#### **2. GitHub Actions Not Triggering**
- Check `RENDER_APP_URL` secret is set correctly
- Verify workflow is enabled
- Check cron schedule (4:45 PM PT = 11:45 PM UTC)

#### **3. Refresh Fails**
- Check Render app logs
- Verify Yahoo Finance API is accessible
- Check database connection

### **Debug Commands:**
```bash
# Check app health
curl https://your-app.onrender.com/api/health

# Manual refresh
curl -X POST https://your-app.onrender.com/api/refresh

# Check database status
curl https://your-app.onrender.com/api/status
```

## 🎉 **Success!**

Your stock ticker now has:
- ✅ **Instant page loads** (no 7-minute waits)
- ✅ **Daily fresh data** (4:45 PM PT refresh)
- ✅ **Persistent storage** (PostgreSQL)
- ✅ **Completely free** (all free tiers)
- ✅ **Reliable operation** (GitHub Actions + Render)

**Your app is now production-ready with professional-grade reliability!**
