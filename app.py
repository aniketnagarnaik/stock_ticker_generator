"""
Stock Data Viewer - Production Flask App
Clean, simple implementation for viewing real stock data
"""

from flask import Flask, render_template, jsonify, request
import os
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

if __name__ == '__main__':
        # Load initial data
        print("Loading initial stock data...")
        stock_data = StockData()
        stocks_data = stock_data.get_all_stocks()
        
        print(f"Loaded {len(stocks_data)} stocks")
        
        # Start the app
        port = int(os.environ.get('PORT', 5000))
        app.run(debug=False, host='0.0.0.0', port=port)
