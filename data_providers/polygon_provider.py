"""
Polygon.io provider for benchmark data (SPY, QQQ, sector ETFs)
Provides real relative strength calculations vs actual benchmarks
"""

import os
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from polygon import RESTClient
from .base_provider import BaseDataProvider


class PolygonProvider(BaseDataProvider):
    """Polygon.io provider for benchmark/ETF data"""
    
    def __init__(self):
        self.api_key = os.getenv('POLYGON_API_KEY')
        self.client = None
        if self.api_key:
            self.client = RESTClient(api_key=self.api_key)
        
        # Benchmark symbols for RS calculations
        self.benchmarks = {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ ETF', 
            'IWM': 'Russell 2000 ETF',
            'XLK': 'Technology Sector ETF',
            'XLE': 'Energy Sector ETF',
            'XLV': 'Healthcare Sector ETF',
            'XLI': 'Industrial Sector ETF',
            'XLY': 'Consumer Discretionary ETF'
        }
        
        # Cache for benchmark data to avoid rate limits
        self._benchmark_cache = {}
        self._last_fetch_time = None
    
    def is_available(self) -> bool:
        """Check if Polygon.io is available"""
        return self.api_key is not None and self.client is not None
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return 'Polygon.io'
    
    def get_benchmark_data(self, symbol: str, days: int = 252) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a benchmark symbol
        
        Args:
            symbol: Benchmark symbol (SPY, QQQ, etc.)
            days: Number of days of historical data
            
        Returns:
            DataFrame with price data or None if error
        """
        if not self.is_available():
            return None
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # Format dates for Polygon API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            # Fetch aggregates (daily bars)
            aggs = self.client.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_str,
                to=end_str,
                limit=50000
            )
            
            if not aggs:
                return None
            
            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append({
                    'date': pd.to_datetime(agg.timestamp, unit='ms').strftime('%Y-%m-%d'),
                    'open': agg.open,
                    'high': agg.high,
                    'low': agg.low,
                    'close': agg.close,
                    'volume': agg.volume
                })
            
            df = pd.DataFrame(data)
            if df.empty:
                return None
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"Error fetching Polygon data for {symbol}: {e}", flush=True)
            return None
    
    def get_all_benchmarks(self, days: int = 252) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for all benchmark symbols
        
        Args:
            days: Number of days of historical data
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        benchmark_data = {}
        
        for symbol in self.benchmarks.keys():
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
    
    def get_all_benchmarks_cached(self, days: int = 252) -> Dict[str, pd.DataFrame]:
        """
        Get historical data for all benchmark symbols with caching to avoid rate limits
        
        Args:
            days: Number of days of historical data
            
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        # Check if we have cached data that's less than 1 hour old
        current_time = time.time()
        if (self._last_fetch_time and 
            current_time - self._last_fetch_time < 3600 and  # 1 hour cache
            self._benchmark_cache):
            print(f"  📊 Using cached benchmark data (age: {int(current_time - self._last_fetch_time)}s)", flush=True)
            return self._benchmark_cache
        
        # Fetch fresh data with rate limiting
        print(f"  📊 Fetching fresh benchmark data from Polygon.io...", flush=True)
        benchmark_data = {}
        
        # Only fetch the most important benchmarks to avoid rate limits
        priority_symbols = ['SPY', 'QQQ']  # Just SPY and QQQ for now
        
        for symbol in priority_symbols:
            print(f"  📊 Fetching {symbol} data from Polygon.io...", flush=True)
            data = self.get_benchmark_data(symbol, days)
            if data is not None:
                benchmark_data[symbol] = data
                print(f"    ✅ {symbol}: {len(data)} days of data", flush=True)
            else:
                print(f"    ❌ {symbol}: No data available", flush=True)
            
            # Rate limiting: 5 calls/minute = 12 seconds between calls
            time.sleep(12)
        
        # Cache the results
        self._benchmark_cache = benchmark_data
        self._last_fetch_time = current_time
        
        return benchmark_data
    
    def calculate_relative_strength(self, stock_prices: pd.DataFrame, 
                                 benchmark_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Calculate relative strength vs benchmarks
        
        Args:
            stock_prices: Stock price DataFrame with 'date' and 'close' columns
            benchmark_data: Dictionary of benchmark DataFrames
            
        Returns:
            Dictionary with RS values vs each benchmark
        """
        if stock_prices.empty or not benchmark_data:
            return {'rs_spy': None, 'rs_sector': None}
        
        try:
            # Prepare stock data
            stock_df = stock_prices.copy()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            stock_df = stock_df.set_index('date')['close']
            
            rs_values = {}
            
            # Calculate RS vs SPY (primary benchmark)
            if 'SPY' in benchmark_data:
                spy_df = benchmark_data['SPY'].copy()
                spy_df['date'] = pd.to_datetime(spy_df['date'])
                spy_df = spy_df.set_index('date')['close']
                
                rs_spy = self._calculate_rs_ratio(stock_df, spy_df)
                rs_values['rs_spy'] = rs_spy
            
            # Calculate RS vs sector ETF (if available)
            # For now, use QQQ as sector proxy for tech stocks
            if 'QQQ' in benchmark_data:
                qqq_df = benchmark_data['QQQ'].copy()
                qqq_df['date'] = pd.to_datetime(qqq_df['date'])
                qqq_df = qqq_df.set_index('date')['close']
                
                rs_sector = self._calculate_rs_ratio(stock_df, qqq_df)
                rs_values['rs_sector'] = rs_sector
            
            return rs_values
            
        except Exception as e:
            print(f"Error calculating relative strength: {e}", flush=True)
            return {'rs_spy': None, 'rs_sector': None}
    
    def _calculate_rs_ratio(self, stock_prices: pd.Series, benchmark_prices: pd.Series) -> Optional[float]:
        """
        Calculate relative strength ratio between stock and benchmark
        
        Args:
            stock_prices: Stock price series
            benchmark_prices: Benchmark price series
            
        Returns:
            RS ratio or None if calculation fails
        """
        try:
            # Align dates (inner join to get common dates)
            aligned_data = pd.DataFrame({
                'stock': stock_prices,
                'benchmark': benchmark_prices
            }).dropna()
            
            if len(aligned_data) < 50:  # Need at least 50 days of data
                return None
            
            # Calculate returns
            stock_returns = aligned_data['stock'].pct_change().dropna()
            benchmark_returns = aligned_data['benchmark'].pct_change().dropna()
            
            # Align returns
            returns_data = pd.DataFrame({
                'stock': stock_returns,
                'benchmark': benchmark_returns
            }).dropna()
            
            if len(returns_data) < 30:
                return None
            
            # Calculate relative strength using weighted periods
            # Standard RS calculation: 3, 6, 9, 12 month periods
            periods = {
                63: 0.25,   # ~3 months
                126: 0.25,  # ~6 months  
                189: 0.25,  # ~9 months
                252: 0.25   # ~12 months
            }
            
            total_rs = 0
            valid_periods = 0
            
            for days, weight in periods.items():
                if len(returns_data) >= days:
                    # Get last N days of returns
                    stock_period = returns_data['stock'].tail(days)
                    benchmark_period = returns_data['benchmark'].tail(days)
                    
                    # Calculate cumulative returns
                    stock_cum_return = (1 + stock_period).prod() - 1
                    benchmark_cum_return = (1 + benchmark_period).prod() - 1
                    
                    # Calculate RS for this period
                    if benchmark_cum_return != 0:
                        period_rs = (stock_cum_return / benchmark_cum_return - 1) * 100
                        total_rs += period_rs * weight
                        valid_periods += 1
            
            if valid_periods == 0:
                return None
            
            # Return weighted average RS
            return round(total_rs, 2)
            
        except Exception as e:
            print(f"Error in RS calculation: {e}", flush=True)
            return None
    
    def get_data_snapshot_date(self) -> Optional[str]:
        """Get the latest data snapshot date from Polygon.io"""
        if not self.is_available():
            return None
        
        try:
            # Get latest data for SPY to determine snapshot date
            spy_data = self.get_benchmark_data('SPY', days=30)
            if spy_data is not None and not spy_data.empty:
                latest_date = spy_data.iloc[-1]['date']
                return latest_date.strftime('%Y-%m-%d')
            return None
        except Exception as e:
            print(f"Error getting data snapshot date: {e}", flush=True)
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        Polygon provider is only for benchmark data, not individual stocks
        This method should not be called directly
        """
        raise NotImplementedError("PolygonProvider is only for benchmark data. Use defeatbeta or yahoo providers for individual stocks.")
    
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        """
        Polygon provider is only for benchmark data, not individual stocks
        This method should not be called directly
        """
        raise NotImplementedError("PolygonProvider is only for benchmark data. Use defeatbeta or yahoo providers for individual stocks.")
