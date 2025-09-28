# 📈 Stock Data Viewer

A clean, simple Flask application for viewing real stock data from Yahoo Finance.

## 🎯 What This Does

- **Fetches real stock data** from Yahoo Finance (free, no API key needed)
- **Shows essential metrics**: Symbol, Company Name, Market Cap, Price, EPS, Sector
- **Clean, simple interface** - professional web interface
- **Easy to extend** - simple code structure

## 📁 File Structure

```
stock_ticker_generator/
├── stock_symbols.txt          # List of stock symbols (4 stocks)
├── stock_data.py             # Yahoo Finance data fetcher
├── app.py                    # Flask web application
├── templates/
│   └── index.html           # Web interface
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip3 install Flask yfinance
```

### 2. Test Data Fetching
```bash
python3 stock_data.py
```

### 3. Start Web App
```bash
python3 app.py
```

### 4. Open Browser
Go to: http://localhost:5000

## 📊 Current Stock List

The app fetches data for 4 major tech stocks:
- **AAPL** - Apple Inc.
- **MSFT** - Microsoft Corporation  
- **GOOGL** - Alphabet Inc.
- **NVDA** - NVIDIA Corporation

## 🔧 How to Add More Stocks

1. **Edit `stock_symbols.txt`** - Add more stock symbols (one per line)
2. **Restart the app** - The new symbols will be loaded automatically

## 📈 Features

- ✅ **Real-time data** from Yahoo Finance
- ✅ **Clean web interface** with Bootstrap styling
- ✅ **Refresh button** to update data
- ✅ **Statistics** (total stocks, average market cap, average EPS)
- ✅ **Responsive design** works on mobile and desktop

## 🎨 Web Interface

The web interface shows:
- **Stock table** with all the essential data
- **Statistics cards** showing totals and averages
- **Refresh button** to update data from Yahoo Finance
- **Clean, professional styling** with Bootstrap

## 🔄 API Endpoints

- `GET /` - Main web page
- `GET /api/stocks` - JSON data of all stocks
- `GET /api/refresh` - Refresh data from Yahoo Finance

## 💡 Why This Approach

- **Simple**: No complex blueprints or multiple files
- **Focused**: Just the essential features you need
- **Extensible**: Easy to add more features
- **Reliable**: Uses proven libraries (Flask, yfinance)
- **Free**: No API keys or costs

## 🚀 Next Steps

1. **Add more stocks** to `stock_symbols.txt`
2. **Customize the interface** in `templates/index.html`
3. **Add filtering** (by sector, market cap, etc.)
4. **Add more data points** (P/E ratio, volume, etc.)
5. **Add database storage** for historical data

## 🐛 Troubleshooting

- **Port 5000 in use?** Change the port in `app.py`
- **Data not loading?** Check your internet connection
- **Template errors?** Make sure `templates/` folder exists

## 📝 Example Output

```
AAPL: Apple Inc.
  Market Cap: $3,791,126,003,712
  Price: $255.46
  EPS: $6.59
  Sector: Technology

MSFT: Microsoft Corporation
  Market Cap: $3,801,767,215,104
  Price: $511.46
  EPS: $13.66
  Sector: Technology
```

This is a clean, production-ready foundation that you can build upon!