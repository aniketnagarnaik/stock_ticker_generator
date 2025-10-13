"""
Stock Data Viewer - Database-Backed Flask App
Clean implementation for viewing stock data from database
"""

from flask import Flask, render_template, jsonify, request
from flask.json.provider import DefaultJSONProvider
import os
import sys
from datetime import datetime
import pytz
import math
from database.database import db_manager
from publisher.data_publisher import DataPublisher

# Custom JSON provider to handle NaN values
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, float) and math.isnan(obj):
            return None
        return super().default(obj)

app = Flask(__name__)
app.json = CustomJSONProvider(app)

# Force stdout to flush immediately (for Render logging)
sys.stdout.flush()
sys.stderr.flush()

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

# Server start time in PST
pst = pytz.timezone('US/Pacific')
server_start_time = datetime.now(pst).strftime('%Y-%m-%d %H:%M PST')

# Data publisher instance
data_publisher = DataPublisher()

@app.route('/')
def index():
    """Main page showing stock data from database"""
    try:
        # Get all stocks from database
        stocks = db_manager.get_all_stocks()
        
        # DEBUG: Check first stock's EMA data
        if stocks:
            print(f"🔍 DEBUG: First stock EMA data: {stocks[0].get('ema_data')}", flush=True)
            print(f"🔍 DEBUG: Type: {type(stocks[0].get('ema_data'))}", flush=True)
            print(f"🔍 DEBUG: Bool: {bool(stocks[0].get('ema_data'))}", flush=True)
        
        # Get refresh status
        refresh_status = data_publisher.get_refresh_status()
        
        # Get database stats
        db_stats = data_publisher.get_database_stats()
        
        return render_template('index.html', 
                             stocks=stocks, 
                             server_start_time=server_start_time,
                             cache_status=refresh_status,
                             db_stats=db_stats)
    
    except Exception as e:
        print(f"Error loading main page: {e}")
        return render_template('index.html', 
                             stocks=[], 
                             server_start_time=server_start_time,
                             cache_status={'status': 'error', 'error': str(e)},
                             db_stats={'total_stocks': 0})

@app.route('/api/stocks')
def api_stocks():
    """API endpoint to get stock data from database"""
    try:
        stocks = db_manager.get_all_stocks()
        return jsonify(stocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST', 'GET'])
def refresh_data():
    """Trigger data refresh - called by GitHub Actions or manual"""
    try:
        print("Data refresh triggered...", flush=True)
        print(f"Current stock count before refresh: {db_manager.get_stock_count()}", flush=True)
        
        success, successful_count, failed_count = data_publisher.publish_all_stocks()
        
        print(f"Refresh completed - Success: {success}, Updated: {successful_count}, Failed: {failed_count}", flush=True)
        
        if success:
            response_data = {
                'message': f'Data refreshed successfully: {successful_count} stocks updated, {failed_count} failed',
                'successful_count': successful_count,
                'failed_count': failed_count,
                'success': True,
                'timestamp': datetime.now(pst).isoformat()
            }
            
            print(f"Returning success response: {response_data}", flush=True)
            
            # For GitHub Actions, return 200 status
            if request.method == 'POST':
                return jsonify(response_data), 200
            else:
                return jsonify(response_data)
        else:
            error_data = {
                'message': 'Failed to refresh data',
                'successful_count': successful_count,
                'failed_count': failed_count,
                'success': False,
                'timestamp': datetime.now(pst).isoformat()
            }
            print(f"Returning error response (success=False): {error_data}", flush=True)
            return jsonify(error_data), 500
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Exception in refresh_data: {e}", flush=True)
        print(f"Traceback:\n{error_trace}", flush=True)
        
        error_data = {
            'message': f'Refresh error: {str(e)}',
            'success': False,
            'timestamp': datetime.now(pst).isoformat(),
            'error_details': error_trace
        }
        return jsonify(error_data), 500

@app.route('/api/status')
def get_status():
    """Get refresh and database status"""
    try:
        refresh_status = data_publisher.get_refresh_status()
        db_stats = data_publisher.get_database_stats()
        
        return jsonify({
            'refresh_status': refresh_status,
            'database_stats': db_stats,
            'server_start_time': server_start_time
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/filter')
def filter_stocks():
    """Filter stocks based on criteria"""
    try:
        # Get all stocks from database
        stocks = db_manager.get_all_stocks()
        
        # Get filter parameters
        metric = request.args.get('metric', 'eps_growth')
        threshold = float(request.args.get('threshold', 25))
        operator = request.args.get('operator', 'greater_than')
        
        filtered_stocks = []
        
        for stock in stocks:
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

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        stock_count = db_manager.get_stock_count()
        return jsonify({
            'status': 'healthy',
            'stock_count': stock_count,
            'timestamp': datetime.now(pst).isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(pst).isoformat()
        }), 500

if __name__ == '__main__':
    # Check if database has data
    stock_count = db_manager.get_stock_count()
    
    if stock_count == 0:
        print("WARNING: No stock data found in database")
        print("Run the scheduler or manual refresh to populate data:")
        print("   python scheduler/scheduler.py")
        print("   python scheduler/refresh_job.py")
    
    print(f"Flask app starting with {stock_count} stocks in database")
    
    # Start the app
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
