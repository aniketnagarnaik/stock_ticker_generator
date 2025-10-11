# 👨‍💻 Developer Guide

## Getting Started

Welcome to the Stock Data Viewer project! This guide will help you understand the codebase, set up your development environment, and contribute effectively.

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend        │    │   Data Source   │
│   (HTML/CSS/JS) │◄──►│   (Flask)        │◄──►│   (Yahoo API)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐             │
         │              │   Cache System   │             │
         │              │   (JSON Files)   │             │
         │              └──────────────────┘             │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Interface│    │   Daily Refresh  │    │   Performance   │
│   (Responsive)  │    │   (Cron Jobs)    │    │   Monitoring    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

1. **Flask Application** (`app.py`): Main web server and API endpoints
2. **Data Fetcher** (`stock_data.py`): Yahoo Finance integration and calculations
3. **Cache Manager** (`cache_manager.py`): File-based caching system
4. **Performance Monitor** (`performance_monitor.py`): Performance tracking
5. **Frontend** (`templates/index.html`): Single-page application

## 🔧 Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- Modern web browser
- Code editor (VS Code recommended)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/aniketnagarnaik/stock_ticker_generator.git
   cd stock_ticker_generator
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python3 app.py
   ```

5. **Access the application**
   Open `http://localhost:5000` in your browser

## 📁 Code Structure

### Backend Files

#### `app.py` - Main Flask Application
- **Purpose**: Web server, routing, and API endpoints
- **Key Functions**:
  - `index()`: Serves main HTML page
  - `refresh_data()`: Triggers data refresh
  - `filter_stocks()`: Applies filters (future)
  - `cache_status()`: Returns cache information
- **Dependencies**: Flask, cache_manager, stock_data

#### `stock_data.py` - Data Processing
- **Purpose**: Yahoo Finance integration and calculations
- **Key Classes**:
  - `StockData`: Main data fetcher class
- **Key Methods**:
  - `get_all_stocks()`: Fetches all stock data
  - `get_stock_info()`: Fetches individual stock data
  - `_calculate_rs()`: Relative strength calculations
  - `_calculate_emas()`: EMA calculations
- **Dependencies**: yfinance, pandas, numpy

#### `cache_manager.py` - Caching System
- **Purpose**: File-based caching for performance
- **Key Classes**:
  - `StockCacheManager`: Cache management
- **Key Methods**:
  - `save_to_cache()`: Saves data to JSON files
  - `load_from_cache()`: Loads data from cache
  - `refresh_cache()`: Updates cache with fresh data
  - `get_cache_status()`: Returns cache metadata
- **Dependencies**: json, os, datetime

### Frontend Files

#### `templates/index.html` - Single Page Application
- **Structure**:
  - HTML structure with Bootstrap
  - CSS with CSS variables for theming
  - JavaScript for interactivity
- **Key Features**:
  - Dark/light mode toggle
  - Real-time filtering
  - EMA modal popups
  - Responsive design

## 🎯 Key Features Implementation

### Dark Mode System

**CSS Variables Approach**:
```css
:root {
  --bg-primary: #f8f9fa;
  --text-primary: #212529;
  /* ... more variables */
}

[data-theme="dark"] {
  --bg-primary: #1a1a1a;
  --text-primary: #ffffff;
  /* ... dark theme variables */
}
```

**JavaScript Toggle**:
```javascript
function toggleTheme() {
  const body = document.body;
  const currentTheme = body.getAttribute('data-theme');
  
  if (currentTheme === 'dark') {
    body.removeAttribute('data-theme');
    localStorage.setItem('theme', 'light');
  } else {
    body.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', 'dark');
  }
}
```

### EMA Calculation System

**Data Fetching**:
```python
def _calculate_emas(self, symbol: str) -> dict:
    """Calculate 8 different EMAs for a stock"""
    emas = {}
    
    # Download historical data for different timeframes
    daily_data = yfinance.download(symbol, period="1y", interval="1d")
    weekly_data = yfinance.download(symbol, period="2y", interval="1wk")
    monthly_data = yfinance.download(symbol, period="5y", interval="1mo")
    
    # Calculate EMAs for each timeframe
    # ... calculation logic
```

### Caching System

**Cache Structure**:
```json
{
  "stocks": [...],
  "metadata": {
    "last_updated": "2025-10-04 21:18 PST",
    "cache_valid": true,
    "total_stocks": 503
  }
}
```

## 🧪 Testing

### Running Tests

```bash
# Test cache system
python3 test_cache_system.py

# Test S&P 500 extractor
python3 scripts/sp500_extractor.py

# Performance testing
python3 -c "
from stock_data import StockData
from performance_monitor import PerformanceMonitor

monitor = PerformanceMonitor()
stock_data = StockData(enable_monitoring=True)
data = stock_data.get_all_stocks()
monitor.print_summary()
"
```

### Test Coverage

- **Unit Tests**: Individual function testing
- **Integration Tests**: API endpoint testing
- **Performance Tests**: Load and memory testing
- **UI Tests**: Manual browser testing

## 🔍 Debugging

### Common Issues

1. **Port 5000 in use**
   ```bash
   lsof -ti:5000 | xargs kill -9
   ```

2. **Cache corruption**
   ```bash
   rm stock_cache.json cache_metadata.json
   ```

3. **Yahoo Finance rate limiting**
   - Check `stock_data.py` rate limiting settings
   - Increase `request_delay` if needed

### Debug Mode

Enable Flask debug mode in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=port)
```

### Logging

Add logging to track issues:
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Processing stock data...")
```

## 🚀 Performance Optimization

### Caching Strategy

1. **File-based Cache**: JSON files for fast access
2. **Cache Validation**: 24-hour expiration
3. **Background Refresh**: Daily cron jobs
4. **Fallback**: Live data if cache unavailable

### API Optimization

1. **Rate Limiting**: 1-second delays between Yahoo Finance calls
2. **Batch Processing**: Bulk data downloads where possible
3. **Error Handling**: Retry logic with exponential backoff
4. **Memory Management**: Efficient data structures

### Frontend Optimization

1. **CSS Variables**: Efficient theme switching
2. **Minimal JavaScript**: Lightweight client-side logic
3. **Responsive Images**: Optimized for mobile
4. **Lazy Loading**: Load data as needed

## 📝 Coding Standards

### Python

- **PEP 8**: Follow Python style guidelines
- **Type Hints**: Use type annotations
- **Docstrings**: Document all functions and classes
- **Error Handling**: Use try-except blocks appropriately

### JavaScript

- **ES6+**: Use modern JavaScript features
- **Consistent Naming**: camelCase for variables, PascalCase for classes
- **Comments**: Explain complex logic
- **Error Handling**: Use try-catch blocks

### CSS

- **CSS Variables**: Use custom properties for theming
- **Mobile First**: Responsive design approach
- **BEM Methodology**: Block-Element-Modifier naming
- **Performance**: Minimize CSS specificity

## 🔄 Git Workflow

### Branch Strategy

- **main**: Production-ready code
- **develop**: Development branch
- **feature/**: Feature branches
- **hotfix/**: Critical bug fixes

### Commit Messages

Use conventional commit format:
```
feat: add dark mode toggle
fix: resolve EMA modal dark mode issue
docs: update API documentation
refactor: optimize cache system
```

### Pull Request Process

1. Create feature branch from `develop`
2. Implement changes with tests
3. Update documentation
4. Submit pull request
5. Code review and approval
6. Merge to `develop`

## 🐛 Troubleshooting

### Common Development Issues

1. **Module Import Errors**
   - Check virtual environment activation
   - Verify package installation
   - Check Python path

2. **Template Not Found**
   - Verify `templates/` directory structure
   - Check Flask app configuration

3. **CSS Not Loading**
   - Check file paths and permissions
   - Verify Bootstrap CDN connectivity

4. **JavaScript Errors**
   - Check browser console
   - Verify function definitions
   - Check for syntax errors

### Performance Issues

1. **Slow Loading**
   - Check cache status
   - Verify network connectivity
   - Monitor memory usage

2. **High Memory Usage**
   - Check for memory leaks
   - Optimize data structures
   - Monitor garbage collection

## 📚 Additional Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Yahoo Finance API**: https://pypi.org/project/yfinance/
- **Bootstrap Documentation**: https://getbootstrap.com/docs/
- **CSS Variables Guide**: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Follow coding standards**
4. **Add tests for new features**
5. **Update documentation**
6. **Submit a pull request**

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Functions are properly documented
- [ ] Tests are included and passing
- [ ] No hardcoded values
- [ ] Error handling is implemented
- [ ] Performance considerations addressed
- [ ] Documentation is updated

## 📞 Getting Help

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and share ideas
- **Code Review**: Request reviews for your changes
- **Documentation**: Check existing docs first

---

**Happy Coding!** 🚀

