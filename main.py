"""
Stock Data Viewer - Production Flask App
Clean, simple implementation for viewing real stock data
"""

from flask import Flask, render_template, jsonify
from stock_data import StockData

app = Flask(__name__)

# Global variable to store stock data
stocks_data = []

@app.route('/')
def index():
    """Main page showing stock data"""
    return render_template('index.html', stocks=stocks_data)

@app.route('/api/stocks')
def api_stocks():
    """API endpoint to get stock data"""
    return jsonify(stocks_data)

@app.route('/api/refresh')
def refresh_data():
    """Refresh stock data from Yahoo Finance"""
    global stocks_data
    
    print("Refreshing stock data...")
    stock_data = StockData()
    stocks_data = stock_data.get_all_stocks()
    
    return jsonify({
        'message': 'Data refreshed successfully',
        'count': len(stocks_data)
    })

if __name__ == '__main__':
    # Load initial data
    print("Loading initial stock data...")
    stock_data = StockData()
    stocks_data = stock_data.get_all_stocks()
    
    print(f"Loaded {len(stocks_data)} stocks")
    
    # Start the app
    app.run(debug=True, host='0.0.0.0', port=5000)
