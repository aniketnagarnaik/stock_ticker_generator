"""
Data Publisher (Refactored)
Uses new clean architecture with DAO, Business Logic, and Provider layers
"""

import os
from typing import List, Dict, Tuple
import numpy as np
from database.models import RefreshLog
from business.data_orchestrator import DataOrchestrator


class DataPublisher:
    """Publishes stock data to database using clean architecture"""
    
    def __init__(self):
        self.orchestrator = DataOrchestrator()
    
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
    
    def publish_all_stocks(self) -> Tuple[bool, int, int]:
        """
        Fetch all stock data and publish to database using new architecture
        
        Returns:
            Tuple of (success, successful_count, failed_count)
        """
        # Create refresh log entry
        session = self.orchestrator.stock_dao.get_session()
        try:
            refresh_log = RefreshLog(status='running')
            session.add(refresh_log)
            session.commit()
            log_id = refresh_log.id
            
            print(f"Starting data refresh (Log ID: {log_id})...", flush=True)
            
            # First, refresh benchmark data if needed
            self.orchestrator.refresh_benchmark_data()
            
            # Get stock symbols to process
            stock_symbols = self._get_stock_symbols()
            
            if not stock_symbols:
                print("No stock symbols to process", flush=True)
                self._update_refresh_log(log_id, 'failed', 0, 0, "No stock symbols to process")
                return False, 0, 0
            
            print(f"Processing {len(stock_symbols)} stocks...", flush=True)
            
            # Process stocks using orchestrator
            successful_count, failed_count = self.orchestrator.process_stock_data(stock_symbols)
            
            # Update refresh log
            if successful_count > 0:
                status = 'completed' if failed_count == 0 else 'completed_with_errors'
                self._update_refresh_log(log_id, status, successful_count, failed_count)
                print(f"Data refresh completed: {successful_count} successful, {failed_count} failed", flush=True)
                return True, successful_count, failed_count
            else:
                self._update_refresh_log(log_id, 'failed', 0, failed_count, "No stocks processed successfully")
                print("Data refresh failed: No stocks processed successfully", flush=True)
                return False, 0, failed_count
                
        except Exception as e:
            print(f"Error during data refresh: {e}", flush=True)
            self._update_refresh_log(log_id, 'failed', 0, 0, str(e))
            return False, 0, 0
        finally:
            session.close()
    
    def _get_stock_symbols(self) -> List[str]:
        """Get list of stock symbols to process"""
        # Check for environment variable to specify stock file
        stock_file = os.getenv('STOCK_SYMBOLS_FILE', 'data/stock_symbols.txt')
        
        try:
            # Read from stock symbols file
            with open(stock_file, 'r') as f:
                symbols = [line.strip().upper() for line in f if line.strip()]
            print(f"📊 Loading {len(symbols)} symbols from {stock_file}", flush=True)
            return symbols
        except FileNotFoundError:
            print(f"⚠️ {stock_file} not found, using test data", flush=True)
            # Fallback to test data
            return ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    def _update_refresh_log(self, log_id: int, status: str, successful_count: int, 
                           failed_count: int, error_message: str = None):
        """Update refresh log entry"""
        session = self.orchestrator.stock_dao.get_session()
        try:
            refresh_log = session.query(RefreshLog).filter(RefreshLog.id == log_id).first()
            if refresh_log:
                refresh_log.status = status
                refresh_log.successful_count = successful_count
                refresh_log.failed_count = failed_count
                refresh_log.error_message = error_message
                if status in ['completed', 'completed_with_errors']:
                    from datetime import datetime
                    refresh_log.completed_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            print(f"Error updating refresh log: {e}", flush=True)
            session.rollback()
        finally:
            session.close()
    
    def get_all_stocks(self) -> List[Dict]:
        """
        Get all stocks data for UI consumption
        
        Returns:
            List of stock dictionaries with metrics
        """
        return self.orchestrator.get_all_stocks_data()
    
    def get_refresh_status(self) -> Dict:
        """
        Get refresh status information
        
        Returns:
            Dictionary with refresh status
        """
        return self.orchestrator.get_refresh_status()
    
    def get_database_stats(self) -> Dict:
        """
        Get database statistics
        
        Returns:
            Dictionary with database stats
        """
        return self.orchestrator.get_database_stats()
    
    def refresh_single_stock(self, symbol: str) -> bool:
        """
        Refresh data for a single stock
        
        Args:
            symbol: Stock symbol to refresh
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Refreshing data for {symbol}...", flush=True)
            
            # Process single stock
            successful_count, failed_count = self.orchestrator.process_stock_data([symbol])
            
            if successful_count > 0:
                print(f"✅ {symbol} refreshed successfully", flush=True)
                return True
            else:
                print(f"❌ {symbol} refresh failed", flush=True)
                return False
                
        except Exception as e:
            print(f"Error refreshing {symbol}: {e}", flush=True)
            return False
