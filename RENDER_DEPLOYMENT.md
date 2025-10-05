# Render Deployment Guide - Daily Stock Data Refresh

## 🚀 **Deployment Overview**

This guide explains how to deploy the stock ticker application with daily data refresh on Render.

## 📋 **Deployment Steps**

### **Step 1: Deploy to Render**

1. **Connect GitHub Repository**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Select the `stock_ticker_generator` repository

2. **Configure Web Service**
   ```
   Name: stock-ticker-web
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python app.py
   Plan: Free
   ```

3. **Set Environment Variables**
   ```
   PYTHON_VERSION=3.11.5
   PORT=10000
   ```

### **Step 2: Deploy Cron Job**

1. **Create Cron Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Cron Job"
   - Connect the same GitHub repository

2. **Configure Cron Job**
   ```
   Name: stock-data-refresh
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python daily_refresh_job.py
   Schedule: 0 23 * * *  (11 PM UTC = 6 PM ET)
   Plan: Free
   ```

3. **Set Environment Variables**
   ```
   PYTHON_VERSION=3.11.5
   STOCK_APP_URL=https://stock-ticker-web.onrender.com
   ```

## ⏰ **Schedule Details**

### **Daily Refresh Schedule**
- **Time**: 11 PM UTC (6 PM ET) - After US market close
- **Frequency**: Daily
- **Duration**: ~10-15 minutes
- **Purpose**: Update stock data cache with fresh Yahoo Finance data

### **Market Hours Consideration**
- **US Market Close**: 4 PM ET
- **After Hours Trading**: Until 8 PM ET
- **Refresh Time**: 6 PM ET (allows 2 hours for after-hours data)

## 🔧 **How It Works**

### **Daily Workflow**
1. **6 PM ET**: Cron job starts
2. **Data Fetch**: Downloads fresh data from Yahoo Finance (503 stocks)
3. **Cache Update**: Saves data to `stock_cache.json`
4. **Web App**: Automatically serves cached data (fast loading)
5. **User Experience**: Fast page loads with fresh daily data

### **Fallback System**
- **Cache Miss**: If cache is invalid, fetches live data
- **Rate Limiting**: Handles Yahoo Finance API limits gracefully
- **Error Handling**: Comprehensive error recovery and logging

## 📊 **Performance Benefits**

### **Before Caching**
- ❌ 10-15 minute page load time
- ❌ 2000+ API calls on every visit
- ❌ Poor user experience

### **After Caching**
- ✅ 2-3 second page load time
- ✅ 0 API calls for users
- ✅ Excellent user experience
- ✅ Daily fresh data

## 🛠 **Monitoring & Maintenance**

### **Check Job Status**
```bash
# View cron job logs in Render dashboard
# Or check cache status via API
curl https://stock-ticker-web.onrender.com/api/cache/status
```

### **Manual Refresh**
```bash
# Trigger manual refresh
curl -X POST https://stock-ticker-web.onrender.com/api/refresh
```

### **Cache Management**
```bash
# Clear cache (admin only)
curl -X POST https://stock-ticker-web.onrender.com/api/cache/clear
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Rate Limiting**
   - **Symptom**: "Too Many Requests" errors
   - **Solution**: Cron job uses exponential backoff and retries
   - **Fallback**: Partial data is still cached

2. **Cache Not Updating**
   - **Check**: Cron job logs in Render dashboard
   - **Verify**: Environment variables are set correctly
   - **Manual**: Trigger refresh via API endpoint

3. **Slow Loading**
   - **Check**: Cache status endpoint
   - **Verify**: Cache file exists and is valid
   - **Fallback**: App will fetch live data if cache fails

### **Logs to Monitor**
- **Web App**: Application startup and cache loading
- **Cron Job**: Daily refresh progress and performance
- **API Calls**: Rate limiting and error handling

## 📈 **Scaling Considerations**

### **Current Limits (Free Plan)**
- **Web Service**: 750 hours/month
- **Cron Job**: 750 hours/month
- **Data Processing**: ~500 stocks efficiently

### **Upgrade Options**
- **Paid Plans**: Higher limits, better performance
- **Database**: Move from file cache to database
- **CDN**: Add content delivery network for global performance

## 🔐 **Security Notes**

### **API Endpoints**
- **Public**: `/`, `/api/stocks`, `/api/cache/status`
- **Admin**: `/api/refresh`, `/api/cache/clear`
- **Rate Limited**: All endpoints have built-in protection

### **Data Privacy**
- **No User Data**: Application doesn't store personal information
- **Public Data**: All stock data is publicly available
- **Cache Files**: Temporary, automatically managed

## ✅ **Verification Checklist**

- [ ] Web service deployed and accessible
- [ ] Cron job scheduled and running
- [ ] Cache status shows valid data
- [ ] Page loads in <5 seconds
- [ ] Daily refresh completes successfully
- [ ] Error handling works for rate limits
- [ ] Fallback to live data works when needed

---

**🎉 Your stock ticker application is now running with daily data refresh!**

**Access your app**: `https://stock-ticker-web.onrender.com`
**Monitor jobs**: Render Dashboard → Cron Jobs
**Check status**: `https://stock-ticker-web.onrender.com/api/cache/status`
