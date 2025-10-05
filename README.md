# 📈 Stock Data Viewer

A comprehensive stock analysis web application that provides real-time stock data, technical analysis, and filtering capabilities for S&P 500 companies.

## 🚀 Features

### 📊 **Data Analysis**
- **503 S&P 500 Stocks**: Complete list with real-time data from Yahoo Finance
- **EPS Growth Analysis**: Quarter-over-quarter earnings growth tracking
- **Relative Strength (RS)**: Weighted RS calculations vs SPY and sector ETFs
- **EMA Technical Analysis**: 8 different Exponential Moving Averages (Daily, Weekly, Monthly)

### 🎨 **User Experience**
- **Dark/Light Mode**: Professional theme switching with persistent preferences
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Real-time Filtering**: Multiple filter combinations with AND logic
- **Interactive Charts**: Detailed EMA analysis with popup modals

### ⚡ **Performance**
- **Caching System**: File-based caching for faster load times
- **Daily Refresh**: Automated data updates at 8 PM ET
- **Rate Limiting**: Optimized API calls to prevent throttling
- **Memory Efficient**: Handles 500+ stocks with minimal resource usage

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Data Source**: Yahoo Finance API (yfinance)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Deployment**: Render (Web Service + Cron Jobs)
- **Caching**: JSON file-based system
- **Version Control**: Git + GitHub

## 📋 Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git
- Modern web browser

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/aniketnagarnaik/stock_ticker_generator.git
cd stock_ticker_generator
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python3 app.py
```

### 4. Access the Application
Open your browser and navigate to: `http://localhost:5000`

## 📁 Project Structure

```
stock_ticker_generator/
├── 📄 app.py                    # Main Flask application
├── 📄 stock_data.py             # Yahoo Finance data fetcher
├── 📄 cache_manager.py          # Caching system
├── 📄 performance_monitor.py    # Performance tracking
├── 📄 daily_refresh_job.py      # Daily refresh script
├── 📄 stock_symbols.txt         # S&P 500 stock symbols
├── 📄 sp500_companies.json      # Company metadata
├── 📄 requirements.txt          # Python dependencies
├── 📄 render.yaml               # Render deployment config
├── 📁 templates/
│   └── 📄 index.html            # Main web interface
├── 📁 docs/                     # Documentation
│   ├── 📄 API.md               # API documentation
│   ├── 📄 DEPLOYMENT.md        # Deployment guide
│   └── 📄 DEVELOPER_GUIDE.md   # Developer onboarding
├── 📁 config/                   # Configuration files
│   └── 📄 settings.py          # App configuration
└── 📁 scripts/                  # Utility scripts
    └── 📄 sp500_extractor.py    # S&P 500 data extractor
```

## 🔧 Configuration

### Environment Variables
- `PORT`: Server port (default: 5000)
- `PYTHON_VERSION`: Python version for deployment (default: 3.11.5)
- `STOCK_APP_URL`: URL for daily refresh job

### Cache Settings
- Cache files: `stock_cache.json`, `cache_metadata.json`
- Cache validity: 24 hours
- Auto-refresh: Daily at 8 PM ET

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main application interface |
| `/api/stocks` | GET | Get all stock data (JSON) |
| `/api/refresh` | POST | Refresh data from Yahoo Finance |
| `/api/filter` | POST | Apply filters to stock data |
| `/api/cache/status` | GET | Get cache status information |
| `/api/cache/clear` | POST | Clear cached data |

## 🎯 Key Features Explained

### 📈 **EMA Analysis**
- **8 EMAs**: D_9EMA, D_21EMA, D_50EMA, W_9EMA, W_21EMA, W_50EMA, M_9EMA, M_21EMA
- **Signal Generation**: Bullish (above all), Bearish (below all), Mixed (some above/below)
- **Interactive Details**: Click EMA signal for detailed breakdown

### 🔍 **Filtering System**
- **EPS Growth**: Quarter-over-quarter earnings growth
- **Relative Strength**: Performance vs SPY and sector ETFs
- **EMA Filters**: Individual EMA > Price conditions
- **Ticker Search**: Symbol-based filtering
- **Multiple Filters**: AND logic combination

### 💾 **Caching System**
- **File-based**: JSON storage for fast access
- **Metadata Tracking**: Cache age and validity
- **Auto-refresh**: Daily updates via Render cron jobs
- **Fallback**: Live data if cache unavailable

## 🚀 Deployment

### Render Deployment
1. Connect GitHub repository to Render
2. Configure web service with `render.yaml`
3. Set up daily cron job for data refresh
4. Configure environment variables

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 🧪 Testing

### Local Testing
```bash
# Test cache system
python3 test_cache_system.py

# Test S&P 500 extractor
python3 scripts/sp500_extractor.py

# Run performance tests
python3 -c "from performance_monitor import PerformanceMonitor; pm = PerformanceMonitor()"
```

### Performance Metrics
- **Load Time**: < 2 seconds with cache
- **Memory Usage**: ~50MB for 503 stocks
- **API Calls**: Optimized to ~8 calls per stock
- **Processing Speed**: ~80 stocks per minute

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the coding standards
4. Add tests for new features
5. Submit a pull request

See [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for detailed guidelines.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Yahoo Finance**: For providing free stock data API
- **Bootstrap**: For responsive UI components
- **Render**: For hosting and deployment services
- **S&P 500**: For the comprehensive stock list

## 📞 Support

For questions, issues, or contributions:
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: [Your Email]

---

**Last Updated**: October 2025  
**Version**: 2.0.0  
**Status**: Production Ready ✅