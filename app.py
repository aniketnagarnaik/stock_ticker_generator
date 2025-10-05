"""
Stock Data Viewer - Production Flask App
Clean, simple implementation for viewing real stock data
"""

from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime
import pytz
from stock_data import StockData
from cache_manager import StockCacheManager

app = Flask(__name__)

# Custom Jinja2 filter for market cap formatting
@app.template_filter('format_market_cap')
def format_market_cap(market_cap):
    """Format market cap with appropriate units (T, B, MM)"""
    if market_cap >= 1000000000000:
        return f"${market_cap / 1000000000000:.1f}T"
    elif market_cap >= 1000000000:
        return f"${market_cap / 1000000000:.1f}B"
    else:
        return f"${market_cap / 1000000:.0f}MM"

# Global variable to store stock data
stocks_data = []

# Server start time in PST
pst = pytz.timezone('US/Pacific')
server_start_time = datetime.now(pst).strftime('%Y-%m-%d %H:%M PST')

# Cache manager
cache_manager = StockCacheManager()

@app.route('/')
def index():
    """Main page showing stock data"""
    cache_status = cache_manager.get_cache_status()
    return render_template('index.html', 
                         stocks=stocks_data, 
                         server_start_time=server_start_time,
                         cache_status=cache_status)

@app.route('/api/stocks')
def api_stocks():
    """API endpoint to get stock data"""
    return jsonify(stocks_data)

@app.route('/api/refresh')
def refresh_data():
    """Refresh stock data from Yahoo Finance and update cache"""
    global stocks_data
    
    print("Refreshing stock data...")
    fresh_data, success = cache_manager.refresh_cache()
    
    if success:
        stocks_data = fresh_data
        return jsonify({
            'message': 'Data refreshed successfully and cache updated',
            'count': len(stocks_data),
            'cache_updated': True
        })
    else:
        return jsonify({
            'message': 'Failed to refresh data',
            'count': len(stocks_data),
            'cache_updated': False
        }), 500

@app.route('/api/cache/status')
def cache_status():
    """Get cache status information"""
    status = cache_manager.get_cache_status()
    return jsonify(status)

@app.route('/api/cache/clear')
def clear_cache():
    """Clear the cache (admin endpoint)"""
    success = cache_manager.clear_cache()
    return jsonify({
        'message': 'Cache cleared successfully' if success else 'Failed to clear cache',
        'success': success
    })

@app.route('/api/filter')
def filter_stocks():
    """Filter stocks based on EPS growth criteria"""
    try:
        # Get filter parameters
        metric = request.args.get('metric', 'eps_growth')
        threshold = float(request.args.get('threshold', 25))
        operator = request.args.get('operator', 'greater_than')
        
        filtered_stocks = []
        
        for stock in stocks_data:
            if metric == 'eps_growth':
                growth_value = stock.get('eps_growth', {}).get('quarter_over_quarter')
                
                if growth_value is not None:
                    if operator == 'greater_than' and growth_value > threshold:
                        filtered_stocks.append(stock)
                    elif operator == 'less_than' and growth_value < threshold:
                        filtered_stocks.append(stock)
                    elif operator == 'equals' and abs(growth_value - threshold) < 0.01:
                        filtered_stocks.append(stock)
                        
            elif metric == 'rs_spy':
                rs_value = stock.get('relative_strength', {}).get('rs_spy')
                
                if rs_value is not None:
                    if operator == 'greater_than' and rs_value > threshold:
                        filtered_stocks.append(stock)
                    elif operator == 'less_than' and rs_value < threshold:
                        filtered_stocks.append(stock)
                    elif operator == 'equals' and abs(rs_value - threshold) < 0.01:
                        filtered_stocks.append(stock)
                        
            elif metric == 'rs_sector':
                rs_value = stock.get('relative_strength', {}).get('rs_sector')
                
                if rs_value is not None:
                    if operator == 'greater_than' and rs_value > threshold:
                        filtered_stocks.append(stock)
                    elif operator == 'less_than' and rs_value < threshold:
                        filtered_stocks.append(stock)
                    elif operator == 'equals' and abs(rs_value - threshold) < 0.01:
                        filtered_stocks.append(stock)
        
        return jsonify({
            'message': f'Filtered {len(filtered_stocks)} stocks',
            'count': len(filtered_stocks),
            'stocks': filtered_stocks,
            'filter_applied': {
                'metric': metric,
                'threshold': threshold,
                'operator': operator
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Filter error: {str(e)}',
            'count': 0,
            'stocks': []
        }), 400

def load_stock_data():
    """Load stock data from cache or fetch fresh data"""
    global stocks_data
    
    print("🚀 Loading stock data...")
    
    # Try to load from cache first
    cached_data = cache_manager.load_from_cache()
    if cached_data:
        stocks_data = cached_data
        print(f"✅ Loaded {len(stocks_data)} stocks from cache (fast)")
        return
    
    # If no valid cache, fetch fresh data
    print("📡 No valid cache found, fetching fresh data...")
    stock_data = StockData()
    fresh_data = stock_data.get_all_stocks()
    
    if fresh_data:
        stocks_data = fresh_data
        print(f"✅ Loaded {len(stocks_data)} stocks from Yahoo Finance")
        
        # Save to cache for next time
        print("💾 Saving data to cache...")
        cache_manager.save_to_cache(stocks_data)
    else:
        print("❌ Failed to load stock data")
        stocks_data = []

if __name__ == '__main__':
    # Load initial data (from cache if available)
    load_stock_data()
    
    # Start the app
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
