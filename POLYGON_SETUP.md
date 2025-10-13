# Polygon.io Setup for Real Relative Strength Calculations

## Overview

This application now supports **real relative strength calculations** using Polygon.io's free tier for benchmark data (SPY, QQQ, sector ETFs). This replaces the previous fake/mock RS calculations with actual performance comparisons against real market benchmarks.

## Benefits

✅ **Real RS vs SPY**: Actual comparison against S&P 500 ETF  
✅ **Real RS vs Sector**: Actual comparison against sector ETFs  
✅ **Free Tier**: No cost for basic indices data  
✅ **No Rate Limits**: 5 calls/minute is sufficient for daily refresh  
✅ **Reliable Data**: Professional financial data provider  

## Setup Instructions

### 1. Create Polygon.io Account

1. Go to [Polygon.io](https://polygon.io/)
2. Click "Sign Up" 
3. Choose the **Indices Basic Plan** (Free - $0/month)
4. Verify your email

### 2. Get Your API Key

1. Log into your Polygon.io dashboard
2. Go to "API Keys" section
3. Copy your API key (starts with something like `abc123...`)

### 3. Set Environment Variable

#### For Local Development:
```bash
export POLYGON_API_KEY="your_api_key_here"
```

#### For Render Deployment:
1. Go to your Render web service settings
2. Add environment variable:
   - **Key**: `POLYGON_API_KEY`
   - **Value**: `your_api_key_here`

### 4. Test the Setup

Restart your Flask application and check the logs:

```bash
python3 app.py
```

You should see:
```
📡 Data Provider Status:
   • defeatbeta-api: ✅ Available
   • Yahoo Finance: ✅ Available
   • Polygon.io: ✅ Available
```

## How It Works

### Hybrid Data Architecture:
- **defeatbeta-api**: Individual stock data (AAPL, MSFT, etc.) - FREE
- **Polygon.io**: Benchmark data (SPY, QQQ, sector ETFs) - FREE

### Relative Strength Calculation:
1. Fetches 1 year of historical data for benchmarks (SPY, QQQ, etc.)
2. Calculates weighted RS using 3, 6, 9, and 12-month periods
3. Compares stock performance vs actual benchmark performance
4. Returns real percentage differences

### Fallback Behavior:
- If Polygon.io is not configured → Shows "N/A" for RS values
- If Polygon.io fails → Shows "N/A" for RS values  
- No fake/mock calculations - only real benchmark data or N/A

## Free Tier Limits

**Polygon.io Indices Basic (Free)**:
- ✅ Limited Index Tickers (includes SPY, QQQ, major sector ETFs)
- ✅ 5 API Calls / Minute (sufficient for daily refresh)
- ✅ 1+ Year Historical Data
- ✅ End of Day Data
- ✅ Reference Data
- ✅ Technical Indicators

## Troubleshooting

### Issue: "Polygon.io: ❌ Not configured"
**Solution**: Set the `POLYGON_API_KEY` environment variable

### Issue: "No benchmark data available"
**Solution**: Check your Polygon.io account status and API key validity

### Issue: Rate limiting errors
**Solution**: The system now includes rate limiting (12 seconds between calls) and caching (1 hour) to stay within the 5 calls/minute limit

## Cost

**Total Cost: $0/month**
- defeatbeta-api: Free
- Polygon.io Indices Basic: Free
- Render PostgreSQL: Free
- Render Web Service: Free

Perfect for personal projects and small applications!
