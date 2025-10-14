"""
Polygon.io Data Provider (Refactored)
Fetches benchmark/ETF data only - no business logic
"""

import os
import pandas as pd
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from data_providers.base_provider import BaseDataProvider

try:
    from polygon import RESTClient
    POLYGON_AVAILABLE = True
except ImportError:
    POLYGON_AVAILABLE = False
    print("⚠️ polygon-api-client not installed. Install with: pip install polygon-api-client", flush=True)


class PolygonProvider(BaseDataProvider):
    """Polygon.io provider for benchmark/ETF data - Raw data only"""
    
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        self.client = None
        if self.api_key:
            try:
                self.client = RESTClient(api_key=self.api_key)
                print("Polygon.io client initialized successfully.", flush=True)
            except Exception as e:
                print(f"Failed to initialize Polygon.io client: {e}", flush=True)
                self.client = None
        else:
            print("POLYGON_API_KEY not found. Polygon.io provider is not available.", flush=True)
    
    def is_available(self) -> bool:
        """Check if Polygon.io is configured and available"""
        return POLYGON_AVAILABLE and self.client is not None
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "Polygon.io"
    
    def get_benchmark_data(self, symbol: str, days: int = 252) -> Optional[pd.DataFrame]:
        """
        Get raw historical data for a benchmark symbol
        
        Args:
            symbol: Benchmark symbol (e.g., 'SPY', 'QQQ')
            days: Number of days of historical data
            
        Returns:
            DataFrame with historical data or None if failed
        """
        if not self.is_available():
            return None
        
        try:
            # Calculate start date
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days + 30)  # Extra buffer
            
            print(f"    📊 Fetching {symbol} data from {start_date} to {end_date}...", flush=True)
            
            # Fetch data from Polygon.io
            aggs = self.client.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_date,
                to=end_date,
                limit=50000
            )
            
            if not aggs:
                print(f"      ❌ No data returned for {symbol}", flush=True)
                return None
            
            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append({
                    'date': datetime.fromtimestamp(agg.timestamp / 1000).strftime('%Y-%m-%d'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            df = pd.DataFrame(data)
            
            if df.empty:
                print(f"      ❌ Empty DataFrame for {symbol}", flush=True)
                return None
            
            # Sort by date and take only the requested number of days
            df = df.sort_values('date').tail(days)
            
            print(f"      ✅ {symbol}: {len(df)} days of data", flush=True)
            return df
            
        except Exception as e:
            print(f"      ❌ Error fetching {symbol} data: {e}", flush=True)
            return None
    
    def get_all_benchmarks_cached(self, days: int = 252) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for all benchmark symbols with caching
        
        Args:
            days: Number of days of historical data
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        # Define benchmark symbols to fetch
        benchmarks = {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ ETF'
        }
        
        benchmark_data = {}
        
        for symbol in benchmarks.keys():
            print(f"  📊 Fetching {symbol} data from Polygon.io...", flush=True)
            data = self.get_benchmark_data(symbol, days)
            if data is not None:
                benchmark_data[symbol] = data
                print(f"    ✅ {symbol}: {len(data)} days of data", flush=True)
            else:
                print(f"    ❌ {symbol}: No data available", flush=True)
            
            # Rate limiting: 5 calls/minute = 12 seconds between calls
            time.sleep(12)
        
        return benchmark_data
    
    def get_data_snapshot_date(self) -> Optional[str]:
        """Get the latest data snapshot date from SPY"""
        if not self.is_available():
            return None
        
        try:
            # Get latest SPY data
            spy_data = self.get_benchmark_data('SPY', days=5)
            if spy_data is not None and not spy_data.empty:
                latest_date = spy_data.iloc[-1]['date']
                return latest_date
            return None
        except Exception as e:
            print(f"Error getting data snapshot date from Polygon.io: {e}", flush=True)
            return None
    
    # Abstract methods from BaseDataProvider - not applicable for Polygon.io
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Not applicable for Polygon.io - only provides benchmark data"""
        raise NotImplementedError("Polygon.io provider only provides benchmark data")
    
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        """Not applicable for Polygon.io - only provides benchmark data"""
        raise NotImplementedError("Polygon.io provider only provides benchmark data")
