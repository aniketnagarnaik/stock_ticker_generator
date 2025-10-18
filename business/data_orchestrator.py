"""
Business logic for data orchestration and coordination between layers
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
from dao.stock_dao import StockDAO
from dao.stock_metrics_dao import StockMetricsDAO
from dao.index_dao import IndexDAO
from business.calculations import FinancialCalculations
from business.sector_mapper import SectorMapper
from data_providers.provider_manager import ProviderManager


class DataOrchestrator:
    """Orchestrates data flow between providers, business logic, and DAO layers"""
    
    def __init__(self):
        self.stock_dao = StockDAO()
        self.metrics_dao = StockMetricsDAO()
        self.index_dao = IndexDAO()
        self.calculations = FinancialCalculations()
        self.sector_mapper = SectorMapper()
        self.provider_manager = ProviderManager()
    
    def refresh_benchmark_data(self) -> bool:
        """
        Refresh benchmark indices data from Polygon.io
        Uses SectorMapper to determine which ETFs to fetch
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print("📊 Refreshing benchmark indices data...", flush=True)
            
            # Check if we have Polygon.io available
            polygon_provider = self.provider_manager.polygon
            
            if not polygon_provider.is_available():
                print("  ⚠️ Polygon.io not available, skipping benchmark refresh", flush=True)
                return False
            
            # Build benchmarks dictionary from SectorMapper
            benchmarks = {
                'SPY': 'S&P 500 ETF',
                'QQQ': 'NASDAQ ETF'
            }
            
            # Add all sector ETFs from SectorMapper
            for sector, etf in self.sector_mapper.sector_etf_map.items():
                benchmarks[etf] = f'{sector} ETF'
            
            success_count = 0
            for symbol, name in benchmarks.items():
                # Check if data is fresh (less than 24 hours old)
                if self.index_dao.is_data_fresh(symbol, max_age_hours=24):
                    print(f"  ✅ {symbol} data is fresh, skipping", flush=True)
                    success_count += 1
                    continue
                
                print(f"  📊 Fetching {symbol} data from Polygon.io...", flush=True)
                
                # Fetch data from Polygon.io
                price_data = polygon_provider.get_benchmark_data(symbol, days=252)
                
                if price_data is not None:
                    # Convert DataFrame to dictionary format for storage
                    price_data_copy = price_data.copy()
                    
                    # Convert date column to string if it's datetime
                    if pd.api.types.is_datetime64_any_dtype(price_data_copy['date']):
                        price_data_copy['date'] = price_data_copy['date'].dt.strftime('%Y-%m-%d')
                    # If already string, ensure it's in correct format
                    elif price_data_copy['date'].dtype == 'object':
                        price_data_copy['date'] = price_data_copy['date'].astype(str)
                    
                    data_dict = {
                        'data': price_data_copy.to_dict('records'),
                        'last_updated': pd.Timestamp.now().isoformat(),
                        'count': len(price_data)
                    }
                    
                    # Save to database
                    if self.index_dao.upsert_index(symbol, name, data_dict):
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
    
    def process_stock_data(self, stock_symbols: List[str]) -> Tuple[int, int]:
        """
        Process stock data for given symbols
        
        Args:
            stock_symbols: List of stock symbols to process
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        successful_count = 0
        failed_count = 0
        
        print(f"Processing {len(stock_symbols)} stocks...", flush=True)
        
        # Use a single session for all operations (like the old implementation)
        session = self.stock_dao.get_session()
        
        try:
            for symbol in stock_symbols:
                try:
                    print(f"Processing: {symbol}", flush=True)
                    
                    # Get stock data from provider
                    stock_data = self.provider_manager.get_stock_info(symbol)
                    
                    if not stock_data:
                        print(f"  ❌ {symbol}: No data available", flush=True)
                        failed_count += 1
                        continue
                    
                    # Process single stock with session
                    self._process_single_stock(session, symbol, stock_data)
                    
                    print(f"  ✅ {symbol}: Data processed successfully", flush=True)
                    successful_count += 1
                    
                except Exception as e:
                    print(f"  ❌ {symbol}: Error processing - {e}", flush=True)
                    session.rollback()
                    failed_count += 1
        finally:
            session.close()
        
        return successful_count, failed_count
    
    def _process_single_stock(self, session, symbol: str, stock_data: Dict):
        """Process a single stock within the given session"""
        from database.models import Stock, StockMetrics
        import numpy as np
        
        # Helper function to convert numpy types
        def convert_numpy(value):
            if isinstance(value, (np.integer, np.floating)):
                return value.item()
            return value
        
        # Check if stock exists
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            # Create new stock
            stock = Stock(
                symbol=symbol,
                company_name=stock_data.get('company_name', ''),
                sector=stock_data.get('sector'),
                industry=stock_data.get('industry'),
                market_cap=convert_numpy(stock_data.get('market_cap')),
                current_price=convert_numpy(stock_data.get('price'))
            )
            session.add(stock)
        else:
            # Update existing stock
            stock.company_name = stock_data.get('company_name', '')
            stock.sector = stock_data.get('sector')
            stock.industry = stock_data.get('industry')
            stock.market_cap = convert_numpy(stock_data.get('market_cap'))
            stock.current_price = convert_numpy(stock_data.get('price'))
        
        # Commit stock changes
        session.commit()
        
        # Get stock ID immediately after commit (before object expires)
        stock_id = stock.id
        
        # Calculate metrics
        metrics = self._calculate_stock_metrics(symbol, stock_data)
        
        # Check if metrics exist
        stock_metrics = session.query(StockMetrics).filter(StockMetrics.symbol == symbol).first()
        
        if not stock_metrics:
            # Create new metrics
            stock_metrics = StockMetrics(
                symbol=symbol,
                stock_id=stock_id,
                eps_growth_qoq=convert_numpy(metrics.get('eps_growth_qoq')),
                eps_growth_yoy=convert_numpy(metrics.get('eps_growth_yoy')),
                latest_quarterly_eps=convert_numpy(metrics.get('latest_eps')),
                rs_spy=convert_numpy(metrics.get('rs_spy')),
                rs_sector=convert_numpy(metrics.get('rs_sector'))
            )
            if metrics.get('ema_data'):
                stock_metrics.set_ema_data(metrics.get('ema_data'))
            if metrics.get('eps_history'):
                stock_metrics.set_eps_history(metrics.get('eps_history'))
            session.add(stock_metrics)
        else:
            # Update existing metrics
            stock_metrics.stock_id = stock_id
            stock_metrics.eps_growth_qoq = convert_numpy(metrics.get('eps_growth_qoq'))
            stock_metrics.eps_growth_yoy = convert_numpy(metrics.get('eps_growth_yoy'))
            stock_metrics.latest_quarterly_eps = convert_numpy(metrics.get('latest_eps'))
            stock_metrics.rs_spy = convert_numpy(metrics.get('rs_spy'))
            stock_metrics.rs_sector = convert_numpy(metrics.get('rs_sector'))
            if metrics.get('ema_data'):
                stock_metrics.set_ema_data(metrics.get('ema_data'))
            if metrics.get('eps_history'):
                stock_metrics.set_eps_history(metrics.get('eps_history'))
        
        # Commit metrics changes
        session.commit()
    
    def _calculate_stock_metrics(self, symbol: str, stock_data: Dict) -> Dict:
        """
        Calculate all metrics for a stock
        
        Args:
            symbol: Stock symbol
            stock_data: Raw stock data from provider
            
        Returns:
            Dictionary with calculated metrics
        """
        metrics = {}
        
        # Calculate EMA data
        price_data = stock_data.get('price_data')
        if price_data is not None:
            ema_data = self.calculations.calculate_all_emas(price_data)
            metrics['ema_data'] = ema_data
        else:
            metrics['ema_data'] = {}
        
        # Calculate EPS growth
        eps_history = stock_data.get('eps_history', {})
        if eps_history:
            growth_metrics = self.calculations.calculate_eps_growth(eps_history)
            metrics['eps_growth_qoq'] = growth_metrics.get('qoq')
            metrics['eps_growth_yoy'] = growth_metrics.get('yoy')
            metrics['latest_eps'] = growth_metrics.get('latest_eps')
            metrics['eps_history'] = eps_history
        else:
            metrics['eps_growth_qoq'] = None
            metrics['eps_growth_yoy'] = None
            metrics['latest_eps'] = None
            metrics['eps_history'] = {}
        
        # Calculate Relative Strength
        if price_data is not None:
            # Get benchmark data from database
            benchmark_data = self.index_dao.get_all_indices_data()
            
            if benchmark_data:
                # Convert defeatbeta price data to expected format
                price_data_copy = price_data.copy()
                if 'report_date' in price_data_copy.columns:
                    price_data_copy = price_data_copy.rename(columns={'report_date': 'date'})
                
                rs_values = self.calculations.calculate_relative_strength(price_data_copy, benchmark_data)
                metrics['rs_spy'] = rs_values.get('rs_spy')
                metrics['rs_sector'] = rs_values.get('rs_sector')
            else:
                metrics['rs_spy'] = None
                metrics['rs_sector'] = None
        else:
            metrics['rs_spy'] = None
            metrics['rs_sector'] = None
        
        return metrics
    
    def get_all_stocks_data(self) -> List[Dict]:
        """
        Get all stocks data with metrics for UI consumption
        
        Returns:
            List of stock dictionaries with metrics
        """
        return self.metrics_dao.get_combined_stock_data()
    
    def get_refresh_status(self) -> Dict:
        """
        Get refresh status information
        
        Returns:
            Dictionary with refresh status
        """
        try:
            from database.models import RefreshLog
            from sqlalchemy import desc
            
            session = self.stock_dao.get_session()
            
            # Get latest completed refresh
            latest_refresh = session.query(RefreshLog).filter(
                RefreshLog.status == 'completed'
            ).order_by(desc(RefreshLog.completed_at)).first()
            
            if latest_refresh:
                # Convert UTC to PST/PDT for display
                import pytz
                from datetime import datetime
                
                # Database stores in UTC, convert to Pacific time
                utc_time = latest_refresh.completed_at.replace(tzinfo=pytz.UTC)
                pacific = pytz.timezone('US/Pacific')
                pacific_time = utc_time.astimezone(pacific)
                
                # Determine if PST or PDT
                tz_name = pacific_time.strftime('%Z')  # Will be PST or PDT
                
                return {
                    'status': 'completed',
                    'last_updated': pacific_time.strftime(f'%Y-%m-%d %H:%M:%S {tz_name}'),
                    'successful_count': latest_refresh.stocks_successful,
                    'failed_count': latest_refresh.stocks_failed,
                    'cache_valid': self._is_cache_valid(latest_refresh.completed_at)
                }
            else:
                return {
                    'status': 'no_refresh',
                    'last_updated': None,
                    'cache_valid': False
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'cache_valid': False
            }
        finally:
            session.close()
    
    def _is_cache_valid(self, last_updated) -> bool:
        """Check if cache is valid (less than 24 hours old)"""
        from datetime import datetime, timedelta
        return datetime.utcnow() - last_updated < timedelta(hours=24)
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'total_stocks': self.stock_dao.get_stock_count(),
            'total_indices': self.index_dao.get_index_count()
        }
