"""
Data publisher for storing stock data in database
"""

from typing import List, Dict, Tuple
import numpy as np
from database.database import db_manager
from database.models import Stock, StockMetrics, RefreshLog
from database.indices_manager import indices_manager
from data_providers.provider_manager import ProviderManager

class DataPublisher:
    """Publishes stock data to database"""
    
    def __init__(self):
        self.provider_manager = ProviderManager()
    
    @staticmethod
    def _convert_numpy_types(value):
        """Convert numpy types to Python native types for PostgreSQL compatibility"""
        import math
        
        # Handle NaN values (convert to None for JSON compatibility)
        if isinstance(value, float) and math.isnan(value):
            return None
        
        if isinstance(value, (np.integer, np.floating)):
            val = value.item()
            # Check if the converted value is NaN
            if isinstance(val, float) and math.isnan(val):
                return None
            return val
        elif isinstance(value, np.ndarray):
            return value.tolist()
        return value
    
    def refresh_benchmark_data(self) -> bool:
        """
        Refresh benchmark indices data from Polygon.io
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("📊 Refreshing benchmark indices data...", flush=True)
            
            # Check if we have Polygon.io available
            from data_providers.polygon_provider import PolygonProvider
            polygon_provider = PolygonProvider()
            
            if not polygon_provider.is_available():
                print("  ⚠️ Polygon.io not available, skipping benchmark refresh", flush=True)
                return False
            
            # Define benchmark indices to fetch
            benchmarks = {
                'SPY': 'S&P 500 ETF',
                'QQQ': 'NASDAQ ETF'
            }
            
            success_count = 0
            for symbol, name in benchmarks.items():
                # Check if data is fresh (less than 24 hours old)
                if indices_manager.is_index_data_fresh(symbol, max_age_hours=24):
                    print(f"  ✅ {symbol} data is fresh, skipping", flush=True)
                    success_count += 1
                    continue
                
                print(f"  📊 Fetching {symbol} data from Polygon.io...", flush=True)
                
                # Fetch data from Polygon.io
                price_data = polygon_provider.get_benchmark_data(symbol, days=252)
                
                if price_data is not None:
                    # Save to database
                    if indices_manager.save_index_data(symbol, name, price_data):
                        success_count += 1
                    else:
                        print(f"    ❌ Failed to save {symbol} to database", flush=True)
                else:
                    print(f"    ❌ Failed to fetch {symbol} data", flush=True)
                
                # Rate limiting: 12 seconds between calls
                import time
                time.sleep(12)
            
            print(f"📊 Benchmark refresh completed: {success_count}/{len(benchmarks)} successful", flush=True)
            return success_count > 0
            
        except Exception as e:
            print(f"Error refreshing benchmark data: {e}", flush=True)
            return False
    
    def publish_all_stocks(self) -> Tuple[bool, int, int]:
        """
        Fetch all stock data and publish to database
        Returns: (success, successful_count, failed_count)
        """
        # Create refresh log entry
        session = db_manager.get_session()
        try:
            refresh_log = RefreshLog(status='running')
            session.add(refresh_log)
            session.commit()
            log_id = refresh_log.id
            
            print(f"Starting data refresh (Log ID: {log_id})...", flush=True)
            
            # First, refresh benchmark data if needed
            self.refresh_benchmark_data()
            
            # Fetch fresh data using provider manager (defeatbeta primary, Yahoo fallback)
            print("Fetching stock data...", flush=True)
            fresh_data = self.provider_manager.get_all_stocks(use_test_data=True)
            
            print(f"Fetched {len(fresh_data) if fresh_data else 0} stocks", flush=True)
            
            if not fresh_data:
                print("No data fetched from data sources", flush=True)
                refresh_log.mark_completed(0, 0, "Failed to fetch data from Yahoo Finance")
                session.commit()
                return False, 0, 0
            
            # Publish data to database
            successful_count = 0
            failed_count = 0
            
            for stock_data in fresh_data:
                try:
                    self._publish_single_stock(session, stock_data)
                    successful_count += 1
                except Exception as e:
                    print(f"Failed to publish {stock_data.get('symbol', 'unknown')}: {e}")
                    failed_count += 1
            
            # Mark refresh as completed
            refresh_log.mark_completed(successful_count, failed_count)
            session.commit()
            
            print(f"Data refresh completed: {successful_count} successful, {failed_count} failed", flush=True)
            return True, successful_count, failed_count
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Data refresh failed: {e}", flush=True)
            print(f"Traceback:\n{error_trace}", flush=True)
            if 'refresh_log' in locals():
                refresh_log.mark_completed(0, 0, str(e))
                session.commit()
            return False, 0, 0
        finally:
            session.close()
    
    def _publish_single_stock(self, session, stock_data: Dict):
        """Publish a single stock's data to database"""
        symbol = stock_data['symbol']
        
        # Check if stock exists
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            # Create new stock
            stock = Stock(
                symbol=symbol,
                company_name=stock_data['company_name'],
                sector=stock_data.get('sector'),
                industry=stock_data.get('industry'),
                market_cap=self._convert_numpy_types(stock_data.get('market_cap')),
                current_price=self._convert_numpy_types(stock_data.get('price')),
                eps=self._convert_numpy_types(stock_data.get('eps'))
            )
            session.add(stock)
        else:
            # Update existing stock
            stock.company_name = stock_data['company_name']
            stock.sector = stock_data.get('sector')
            stock.industry = stock_data.get('industry')
            stock.market_cap = self._convert_numpy_types(stock_data.get('market_cap'))
            stock.current_price = self._convert_numpy_types(stock_data.get('price'))
            stock.eps = self._convert_numpy_types(stock_data.get('eps'))
            stock.last_updated = stock_data.get('last_updated')
        
        # Commit stock changes
        session.commit()
        
        # Handle metrics
        self._publish_stock_metrics(session, stock, stock_data)
    
    def _publish_stock_metrics(self, session, stock: Stock, stock_data: Dict):
        """Publish stock metrics to database"""
        symbol = stock.symbol
        
        # Check if metrics exist
        metrics = session.query(StockMetrics).filter(StockMetrics.symbol == symbol).first()
        
        if not metrics:
            # Create new metrics
            metrics = StockMetrics(symbol=symbol, stock_id=stock.id)
            session.add(metrics)
        
        # Update EPS growth data
        eps_growth = stock_data.get('eps_growth', {})
        metrics.eps_growth_qoq = self._convert_numpy_types(eps_growth.get('quarter_over_quarter'))
        metrics.eps_growth_yoy = self._convert_numpy_types(eps_growth.get('year_over_year'))
        
        # Update relative strength data
        rs_data = stock_data.get('relative_strength', {})
        metrics.rs_spy = self._convert_numpy_types(rs_data.get('rs_spy'))
        metrics.rs_sector = self._convert_numpy_types(rs_data.get('rs_sector'))
        
        # Update EMA data (convert numpy types)
        ema_data = stock_data.get('ema_data', {})
        if ema_data:
            ema_data_converted = {k: self._convert_numpy_types(v) for k, v in ema_data.items()}
            metrics.set_ema_data(ema_data_converted)
        
        # Update EPS history (convert numpy types in nested dict)
        eps_history = stock_data.get('eps_history', {})
        if eps_history and 'quarterly' in eps_history:
            quarterly_converted = {k: self._convert_numpy_types(v) for k, v in eps_history.get('quarterly', {}).items()}
            eps_history_converted = {'quarterly': quarterly_converted}
            if 'latest_quarterly_eps' in eps_history:
                eps_history_converted['latest_quarterly_eps'] = self._convert_numpy_types(eps_history['latest_quarterly_eps'])
            metrics.set_eps_history(eps_history_converted)
        elif eps_history:
            metrics.set_eps_history(eps_history)
        
        metrics.last_updated = stock_data.get('last_updated')
        
        session.commit()
    
    def get_refresh_status(self) -> Dict:
        """Get status of last refresh operation"""
        session = db_manager.get_session()
        try:
            last_refresh = session.query(RefreshLog).filter(
                RefreshLog.status == 'completed'
            ).order_by(
                RefreshLog.completed_at.desc()
            ).first()
            
            if not last_refresh or not last_refresh.completed_at:
                return {
                    'status': 'never_run',
                    'last_run': None,
                    'last_updated': None,
                    'stocks_processed': 0,
                    'duration_seconds': 0,
                    'cache_valid': False
                }
            
            # Format the completed time in PST
            from datetime import datetime, timedelta
            import pytz
            pst = pytz.timezone('US/Pacific')
            
            # Convert completed_at to PST
            if last_refresh.completed_at.tzinfo is None:
                # Assume UTC if no timezone
                completed_utc = pytz.utc.localize(last_refresh.completed_at)
            else:
                completed_utc = last_refresh.completed_at
            
            completed_pst = completed_utc.astimezone(pst)
            last_updated_str = completed_pst.strftime('%Y-%m-%d %H:%M:%S %Z')
            
            # Check if data is fresh (less than 24 hours old)
            now = datetime.now(pytz.utc)
            age_hours = (now - completed_utc).total_seconds() / 3600
            cache_valid = age_hours < 24
            
            return {
                'status': last_refresh.status,
                'last_run': last_refresh.started_at,
                'completed_at': last_refresh.completed_at,
                'last_updated': last_updated_str,  # Add formatted string for template
                'stocks_processed': last_refresh.stocks_successful + last_refresh.stocks_failed,
                'stocks_successful': last_refresh.stocks_successful,
                'stocks_failed': last_refresh.stocks_failed,
                'duration_seconds': last_refresh.duration_seconds,
                'error_message': last_refresh.error_message,
                'cache_valid': cache_valid  # Add cache validity flag
            }
            
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        session = db_manager.get_session()
        try:
            total_stocks = session.query(Stock).count()
            total_metrics = session.query(StockMetrics).count()
            last_stock_update = session.query(Stock.last_updated).order_by(
                Stock.last_updated.desc()
            ).first()
            
            return {
                'total_stocks': total_stocks,
                'total_metrics': total_metrics,
                'last_stock_update': last_stock_update[0] if last_stock_update else None
            }
            
        finally:
            session.close()
