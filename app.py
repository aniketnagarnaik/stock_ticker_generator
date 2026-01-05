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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database.database import db_manager
from publisher.data_publisher import DataPublisher
from business.data_orchestrator import DataOrchestrator
from business.rrg_calculator import RRGCalculator
from business.trading_signals import TradingSignalsEngine
from database.models import RRGData

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

# Data publisher instance (contains orchestrator)
data_publisher = DataPublisher()
data_orchestrator = data_publisher.orchestrator

# Trading signals engine
trading_signals_engine = TradingSignalsEngine()

@app.route('/')
def home():
    """Home page with navigation to Stock Table and RRG Chart"""
    return render_template('home.html')

@app.route('/stocks')
def stocks_page():
    """Stock table page showing stock data from database"""
    try:
        # Get all stocks data using new architecture
        stocks = data_orchestrator.get_all_stocks_data()
        
        # Get refresh status
        refresh_status = data_orchestrator.get_refresh_status()
        
        # Get database stats
        db_stats = data_orchestrator.get_database_stats()
        
        # Get data snapshot date from the current provider
        data_snapshot_date = None
        try:
            # Use defeatbeta provider directly since it's the primary provider
            defeatbeta_provider = data_orchestrator.provider_manager.defeatbeta
            if defeatbeta_provider and defeatbeta_provider.is_available():
                data_snapshot_date = defeatbeta_provider.get_data_snapshot_date()
        except Exception as e:
            print(f"Could not get data snapshot date: {e}", flush=True)
        
        return render_template('index.html', 
                             stocks=stocks, 
                             server_start_time=server_start_time,
                             cache_status=refresh_status,
                             db_stats=db_stats,
                             data_snapshot_date=data_snapshot_date)
    
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
        stocks = data_orchestrator.get_all_stocks_data()
        return jsonify(stocks)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh', methods=['POST', 'GET'])
def refresh_data():
    """Trigger data refresh - called by GitHub Actions or manual"""
    try:
        print("Data refresh triggered...", flush=True)
        print(f"Current stock count before refresh: {db_manager.get_stock_count()}", flush=True)
        
        # Step 1: Refresh benchmark indices data from Polygon (if stale)
        print("📊 Step 1: Checking benchmark indices freshness...", flush=True)
        benchmark_success = data_orchestrator.refresh_benchmark_data()
        
        if benchmark_success:
            print("✅ Benchmark data is fresh and ready", flush=True)
        else:
            print("⚠️ Benchmark data refresh failed or Polygon not configured, continuing with existing data...", flush=True)
        
        # Step 2: Refresh stock data
        print("📈 Step 2: Refreshing stock data...", flush=True)
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

# RRG Routes
@app.route('/rrg')
def rrg_page():
    """RRG (Relative Rotation Graph) page"""
    return render_template('rrg.html')

@app.route('/api/rrg/data')
def get_rrg_data():
    """Get RRG data from database"""
    try:
        with db_manager.get_session() as session:
            # Get RRG data from database
            rrg_records = session.query(RRGData).order_by(RRGData.symbol).all()
            
            if not rrg_records:
                # No RRG data in database, calculate it
                return calculate_and_return_rrg_data()
            
            # Convert to list of dictionaries
            rrg_data = []
            for record in rrg_records:
                rrg_data.append({
                    'symbol': record.symbol,
                    'name': record.name,
                    'rs_ratio': record.rs_ratio,
                    'rs_momentum': record.rs_momentum,
                    'quadrant': record.quadrant,
                    'current_price': record.current_price,
                    'spy_price': record.spy_price,
                    'week_number': record.week_number,
                    'calculated_at': record.calculated_at.isoformat() if record.calculated_at else None
                })
            
            return jsonify({
                'success': True,
                'rrg_data': rrg_data,
                'count': len(rrg_data)
            })
            
    except Exception as e:
        print(f"Error getting RRG data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rrg/refresh', methods=['POST'])
def refresh_rrg_data():
    """Refresh RRG data by fetching fresh indices from Polygon and recalculating"""
    try:
        # Step 1: Refresh benchmark indices data from Polygon
        print("📊 Step 1: Refreshing benchmark indices from Polygon...", flush=True)
        benchmark_success = data_orchestrator.refresh_benchmark_data()
        
        if not benchmark_success:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh benchmark data from Polygon'
            }), 400
        
        print("✅ Benchmark data refreshed from Polygon", flush=True)
        
        # Step 2: Calculate and save RRG data
        print("📈 Step 2: Calculating RRG data...", flush=True)
        return calculate_and_return_rrg_data()
        
    except Exception as e:
        print(f"❌ Error refreshing RRG data: {e}", flush=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def calculate_and_return_rrg_data():
    """Calculate RRG data from indices and return it"""
    try:
        with db_manager.get_session() as session:
            # Get indices data from database
            from database.models import Index
            indices = session.query(Index).all()
            
            if not indices:
                return jsonify({
                    'success': False,
                    'error': 'No indices data found. Please refresh benchmark data first.'
                }), 400
            
            # Convert to list of dictionaries
            indices_data = []
            for index in indices:
                indices_data.append({
                    'symbol': index.symbol,
                    'name': index.name,
                    'price_data': index.price_data,
                    'last_updated': index.last_updated.isoformat() if index.last_updated else None
                })
            
            # Calculate RRG data with historical trails
            rrg_calculator = RRGCalculator()
            # Calculate 12 weeks so we have 8 weeks with valid momentum (momentum requires 4 weeks of lookback)
            rrg_data = rrg_calculator.calculate_rrg_data(indices_data, weeks_back=12)
            
            if not rrg_data:
                return jsonify({
                    'success': False,
                    'error': 'Failed to calculate RRG data'
                }), 400
            
            # Save to database
            session.query(RRGData).delete()  # Clear existing data
            
            for etf_data in rrg_data:
                rrg_record = RRGData(
                    symbol=etf_data['symbol'],
                    name=etf_data['name'],
                    rs_ratio=etf_data['rs_ratio'],
                    rs_momentum=etf_data['rs_momentum'],
                    quadrant=etf_data['quadrant'],
                    current_price=etf_data['current_price'],
                    spy_price=etf_data['spy_price'],
                    week_number=etf_data.get('week_number', 0)
                )
                session.add(rrg_record)
            
            session.commit()
            
            return jsonify({
                'success': True,
                'rrg_data': rrg_data,
                'count': len(rrg_data),
                'message': 'RRG data calculated and saved successfully'
            })
            
    except Exception as e:
        print(f"Error calculating RRG data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Trading Signals Routes
@app.route('/signals')
def signals_page():
    """Trading Signals Dashboard page"""
    return render_template('signals.html')

def sanitize_for_json(obj):
    """Convert NaN, inf, and other non-JSON-serializable values to None"""
    import math
    import numpy as np
    
    if isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    else:
        return obj

@app.route('/api/signals/data')
def get_trading_signals():
    """Get trading signals for all stocks"""
    try:
        # Get all stocks data with metrics
        stocks_data_raw = data_orchestrator.get_all_stocks_data()
        
        if not stocks_data_raw:
            return jsonify({
                'success': False,
                'error': 'No stock data available',
                'signals': [],
                'summary': {}
            })
        
        # Convert to format expected by trading signals engine
        # The engine expects a list of dicts with 'stock' and 'metrics' keys
        stocks_data_formatted = []
        for stock_data in stocks_data_raw:
            formatted = {
                'stock': {
                    'symbol': stock_data.get('symbol'),
                    'company_name': stock_data.get('company_name'),
                    'sector': stock_data.get('sector'),
                    'industry': stock_data.get('industry'),
                    'current_price': stock_data.get('price'),
                    'market_cap': stock_data.get('market_cap')
                },
                'metrics': {
                    'eps_growth_qoq': stock_data.get('eps_growth', {}).get('quarter_over_quarter'),
                    'eps_growth_yoy': stock_data.get('eps_growth', {}).get('year_over_year'),
                    'latest_quarterly_eps': stock_data.get('eps_growth', {}).get('latest_quarters', [])[-1] if stock_data.get('eps_growth', {}).get('latest_quarters') else None,
                    'rs_spy': stock_data.get('relative_strength', {}).get('rs_spy'),
                    'rs_sector': stock_data.get('relative_strength', {}).get('rs_sector'),
                    'ema_data': stock_data.get('ema_data', {}),
                    'eps_history': stock_data.get('eps_history', {})
                }
            }
            stocks_data_formatted.append(formatted)
        
        # Generate signals for all stocks
        signals = trading_signals_engine.generate_signals_for_all_stocks(stocks_data_formatted)
        
        # Sanitize signals to remove NaN values
        signals = sanitize_for_json(signals)
        
        # Get summary statistics
        summary = trading_signals_engine.get_signal_summary(signals)
        
        return jsonify({
            'success': True,
            'signals': signals,
            'summary': summary,
            'count': len(signals),
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        import traceback
        print(f"Error generating trading signals: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'signals': [],
            'summary': {}
        }), 500

@app.route('/api/signals/refresh', methods=['POST'])
def refresh_trading_signals():
    """Recalculate trading signals (signals are calculated on-demand from DB data)"""
    try:
        # Trading signals are generated from current DB data
        # Just return fresh signals
        return get_trading_signals()
        
    except Exception as e:
        print(f"Error refreshing trading signals: {e}", flush=True)
        return jsonify({
            'success': False,
            'error': str(e)
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
