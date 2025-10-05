"""
Stock Data Fetcher - Yahoo Finance Integration
Clean and focused implementation
"""

import yfinance as yf
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from performance_monitor import PerformanceMonitor


class StockData:
    """Stock data fetcher using Yahoo Finance"""
    
    def __init__(self, enable_monitoring: bool = True):
        self.last_request_time = 0
        self.request_delay = 1.0  # Increased rate limiting for 503 stocks
        self.monitor = PerformanceMonitor() if enable_monitoring else None
        
        # Simple sector to ETF mapping
        self.sector_etf_map = {
            "Industrials": "XLI",
            "Health Care": "XLV", 
            "Healthcare": "XLV",  # Alias for Health Care
            "Technology": "XLK",
            "Utilities": "XLU",
            "Financials": "XLF",
            "Financial Services": "XLF",  # Alias for Financials
            "Materials": "XLB",
            "Consumer Discretionary": "XLY",
            "Consumer Cyclical": "XLY",  # Alias for Consumer Discretionary
            "Real Estate": "XLRE",
            "Communication Services": "XLC",
            "Consumer Staples": "XLP",
            "Consumer Defensive": "XLP",  # Alias for Consumer Staples
            "Energy": "XLE"
        }
    
    def _rate_limit(self):
        """Simple rate limiting to avoid overwhelming Yahoo Finance"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _retry_api_call(self, func, max_retries=3, delay=2):
        """Retry API calls with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if "Rate limited" in str(e) or "Too Many Requests" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)  # Exponential backoff
                        print(f"   ⏳ Rate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        time.sleep(wait_time)
                        continue
                raise e
    
    def _get_historical_eps(self, ticker) -> Dict:
        """Get historical EPS data (quarterly only - optimized)"""
        try:
            eps_data = {
                'quarterly': {},
                'latest_quarterly_eps': None
            }
            
            # Get quarterly EPS data only (annual EPS not used in web interface)
            quarterly_income = ticker.quarterly_income_stmt
            if not quarterly_income.empty and 'Diluted EPS' in quarterly_income.index:
                quarterly_eps = quarterly_income.loc['Diluted EPS'].dropna()
                eps_data['quarterly'] = {str(date.date()): float(value) for date, value in quarterly_eps.items()}
                if len(quarterly_eps) > 0:
                    eps_data['latest_quarterly_eps'] = float(quarterly_eps.iloc[0])
            
            return eps_data
            
        except Exception as e:
            print(f"Error getting historical EPS data: {e}")
            return {'quarterly': {}, 'latest_quarterly_eps': None}
    
    def _calculate_eps_growth(self, eps_history: Dict) -> Dict:
        """Calculate EPS growth percentages from historical data"""
        try:
            growth_data = {
                'quarter_over_quarter': None,
                'year_over_year': None,
                'latest_quarters': []
            }
            
            quarterly_data = eps_history.get('quarterly', {})
            if len(quarterly_data) >= 2:
                # Convert to sorted list by date (most recent first)
                sorted_quarters = sorted(quarterly_data.items(), reverse=True)
                eps_values = [value for _, value in sorted_quarters]
                
                # Calculate quarter-over-quarter growth (most recent vs previous)
                if len(eps_values) >= 2:
                    current_eps = eps_values[0]
                    previous_eps = eps_values[1]
                    if previous_eps != 0:
                        growth_data['quarter_over_quarter'] = ((current_eps - previous_eps) / abs(previous_eps)) * 100
                
                # Calculate year-over-year growth (if we have 4+ quarters)
                if len(eps_values) >= 4:
                    current_eps = eps_values[0]
                    year_ago_eps = eps_values[3]  # 4 quarters ago
                    if year_ago_eps != 0:
                        growth_data['year_over_year'] = ((current_eps - year_ago_eps) / abs(year_ago_eps)) * 100
                
                # Store last 4 quarters for trend analysis
                growth_data['latest_quarters'] = eps_values[:4]
            
            return growth_data
            
        except Exception as e:
            print(f"Error calculating EPS growth: {e}")
            return {'quarter_over_quarter': None, 'year_over_year': None, 'latest_quarters': []}
    
    def _get_sector_etf(self, sector: str) -> str:
        """Get the ETF symbol for a given sector"""
        return self.sector_etf_map.get(sector, "SPY")
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        ema = prices.ewm(span=period).mean()
        return float(ema.iloc[-1])
    
    def _calculate_all_emas(self, symbol: str) -> Dict[str, Optional[float]]:
        """Calculate all EMAs for a symbol - optimized with single download"""
        try:
            # Single download for all timeframes (1 year is sufficient for all EMAs)
            data = yf.download(symbol, period="1y", interval="1d", progress=False)
            if data.empty:
                return self._get_empty_ema_dict()
            
            daily_closes = data['Close']
            
            # Calculate daily EMAs (using daily data directly)
            d_9_ema = self._calculate_ema(daily_closes, 9)
            d_21_ema = self._calculate_ema(daily_closes, 21)
            d_50_ema = self._calculate_ema(daily_closes, 50)
            
            # Resample daily data to weekly (Friday close)
            weekly_data = daily_closes.resample('W-FRI').last().dropna()
            
            # Calculate weekly EMAs
            w_9_ema = self._calculate_ema(weekly_data, 9) if len(weekly_data) >= 9 else None
            w_21_ema = self._calculate_ema(weekly_data, 21) if len(weekly_data) >= 21 else None
            w_50_ema = self._calculate_ema(weekly_data, 50) if len(weekly_data) >= 50 else None
            
            # Resample daily data to monthly (last trading day of month)
            monthly_data = daily_closes.resample('M').last().dropna()
            
            # Calculate monthly EMAs
            m_9_ema = self._calculate_ema(monthly_data, 9) if len(monthly_data) >= 9 else None
            m_21_ema = self._calculate_ema(monthly_data, 21) if len(monthly_data) >= 21 else None
            
            return {
                'D_9EMA': d_9_ema,
                'D_21EMA': d_21_ema,
                'D_50EMA': d_50_ema,
                'W_9EMA': w_9_ema,
                'W_21EMA': w_21_ema,
                'W_50EMA': w_50_ema,
                'M_9EMA': m_9_ema,
                'M_21EMA': m_21_ema
            }
            
        except Exception as e:
            print(f"Error calculating EMAs for {symbol}: {e}")
            return self._get_empty_ema_dict()
    
    def _get_empty_ema_dict(self) -> Dict[str, Optional[float]]:
        """Return empty EMA dictionary"""
        return {
            'D_9EMA': None,
            'D_21EMA': None,
            'D_50EMA': None,
            'W_9EMA': None,
            'W_21EMA': None,
            'W_50EMA': None,
            'M_9EMA': None,
            'M_21EMA': None
        }
    
    def _bulk_download_prices(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """Bulk download 1 year of price data for multiple symbols efficiently"""
        try:
            print(f"Bulk downloading price data for {len(symbols)} symbols...")
            self._rate_limit()
            
            # Use yfinance bulk download with threading for efficiency
            data = yf.download(symbols, period="1y", interval="1d", threads=True, progress=False)
            
            result = {}
            for symbol in symbols:
                if symbol in data.columns.levels[1]:  # Check if symbol exists in multi-level columns
                    symbol_data = data[('Close', symbol)].dropna()
                    prices = []
                    for date, close_price in symbol_data.items():
                        prices.append({
                            'date': date.date(),
                            'close': float(close_price)
                        })
                    result[symbol] = prices
                else:
                    print(f"Warning: No price data found for {symbol}")
                    result[symbol] = []
            
            print(f"Successfully downloaded price data for {len(result)} symbols")
            return result
            
        except Exception as e:
            print(f"Error in bulk download: {e}")
            return {}
    
    def _get_return_from_history(self, prices: List[Dict], months: int) -> Optional[float]:
        """Get % return from today vs N months ago"""
        if not prices or len(prices) == 0:
            return None
        
        today_price = prices[-1]['close']
        target_date = datetime.now().date() - timedelta(days=months * 30)  # Approximate
        
        # Find price closest to or before the target date
        past_price = None
        for price_data in reversed(prices):
            if price_data['date'] <= target_date:
                past_price = price_data['close']
                break
        
        # Fallback to oldest price if nothing matches
        if past_price is None:
            past_price = prices[0]['close']
        
        if past_price == 0:
            return None
            
        return ((today_price - past_price) / past_price) * 100
    
    def _get_unique_sectors_and_etfs(self, stocks_data: List[Dict]) -> List[str]:
        """Get unique sector ETFs needed for the given stocks"""
        etfs = ['SPY']  # Always need SPY
        sectors = set()
        
        for stock in stocks_data:
            sector = stock.get('sector', 'Unknown')
            if sector != 'Unknown':
                sectors.add(sector)
        
        for sector in sectors:
            etf = self._get_sector_etf(sector)
            if etf not in etfs:
                etfs.append(etf)
        
        print(f"Unique sectors found: {list(sectors)}")
        print(f"Sector ETFs needed: {etfs}")
        return etfs
    
    def _calculate_bulk_rs(self, stocks_data: List[Dict]) -> Dict[str, Dict]:
        """Calculate RS for all stocks efficiently using bulk download"""
        try:
            # Get all symbols needed
            stock_symbols = [stock['symbol'] for stock in stocks_data]
            benchmark_symbols = self._get_unique_sectors_and_etfs(stocks_data)
            all_symbols = stock_symbols + benchmark_symbols
            
            # Bulk download all price data
            price_data = self._bulk_download_prices(all_symbols)
            
            if not price_data:
                print("No price data available for RS calculation")
                return {}
            
            # Calculate RS for each stock
            rs_results = {}
            weights = {3: 0.5, 6: 0.3, 9: 0.2}
            
            for stock in stocks_data:
                symbol = stock['symbol']
                sector = stock.get('sector', 'Unknown')
                
                if symbol not in price_data or not price_data[symbol]:
                    rs_results[symbol] = {'rs_spy': None, 'rs_sector': None}
                    continue
                
                ticker_prices = price_data[symbol]
                spy_prices = price_data.get('SPY', [])
                sector_etf = self._get_sector_etf(sector)
                sector_prices = price_data.get(sector_etf, [])
                
                if not spy_prices:
                    rs_results[symbol] = {'rs_spy': None, 'rs_sector': None}
                    continue
                
                rs_spy = 0
                rs_sector = 0
                
                for months, weight in weights.items():
                    ticker_change = self._get_return_from_history(ticker_prices, months)
                    spy_change = self._get_return_from_history(spy_prices, months)
                    sector_change = self._get_return_from_history(sector_prices, months)
                    
                    if ticker_change is not None and spy_change is not None:
                        rs_spy += (ticker_change - spy_change) * weight
                    
                    if ticker_change is not None and sector_change is not None:
                        rs_sector += (ticker_change - sector_change) * weight
                
                rs_results[symbol] = {
                    'rs_spy': round(rs_spy, 2),
                    'rs_sector': round(rs_sector, 2)
                }
            
            return rs_results
            
        except Exception as e:
            print(f"Error in bulk RS calculation: {e}")
            return {}
    
    def _calculate_weighted_rs(self, symbol: str, sector: str) -> Dict:
        """Legacy method - kept for backward compatibility"""
        # This method is now deprecated in favor of bulk calculation
        return {'rs_spy': None, 'rs_sector': None}
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get basic stock information for a symbol"""
        return self._get_stock_info_internal(symbol)
    
    def _get_stock_info_internal(self, symbol: str) -> Optional[Dict]:
        """Internal method for getting stock info"""
        try:
            self._rate_limit()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            if self.monitor:
                self.monitor.record_api_call(success=True, response_time=0.1)
            
            # Get current price
            hist = ticker.history(period="1d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
            if self.monitor:
                self.monitor.record_api_call(success=True, response_time=0.1)
            
            # Calculate market cap
            market_cap = info.get('marketCap', 0)
            if market_cap == 0 and 'sharesOutstanding' in info:
                market_cap = current_price * info['sharesOutstanding']
            
            # Get historical EPS data
            eps_data = self._get_historical_eps(ticker)
            if self.monitor:
                self.monitor.record_api_call(success=True, response_time=0.1)
            
            # Calculate EPS growth
            eps_growth = self._calculate_eps_growth(eps_data)
            
            # Calculate all EMAs
            ema_data = self._calculate_all_emas(symbol)
            if self.monitor:
                self.monitor.record_api_call(success=True, response_time=0.2)
            
            # Calculate Relative Strength (will be done in bulk later)
            rs_data = {'rs_spy': None, 'rs_sector': None}
            
            if self.monitor:
                self.monitor.record_data_processed(1)
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'market_cap': market_cap,
                'eps': info.get('trailingEps', 0),
                'price': current_price,
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'eps_history': eps_data,
                'eps_growth': eps_growth,
                'ema_data': ema_data,
                'relative_strength': rs_data
            }
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            if self.monitor:
                self.monitor.record_error(f"Error getting data for {symbol}: {e}")
            return None
    
    def load_symbols(self, filename: str = 'stock_symbols.txt') -> List[str]:
        """Load stock symbols from file"""
        try:
            with open(filename, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(symbols)} stock symbols: {symbols}")
            return symbols
        except Exception as e:
            print(f"Error loading symbols: {e}")
            return []
    
    def get_all_stocks(self) -> List[Dict]:
        """Get all stocks data with efficient bulk RS calculation"""
        return self._get_all_stocks_internal()
    
    def _get_all_stocks_internal(self) -> List[Dict]:
        """Internal method for getting all stocks data"""
        symbols = self.load_symbols()
        stocks = []
        
        print(f"Fetching basic data for {len(symbols)} stocks...")
        
        for symbol in symbols:
            print(f"Processing: {symbol}")
            
            stock_info = self.get_stock_info(symbol)
            if stock_info:
                stocks.append(stock_info)
            else:
                print(f"  ❌ {symbol}: Failed to get data")
        
        print(f"Successfully loaded {len(stocks)} stocks")
        
        # Calculate RS for all stocks efficiently using bulk download
        if stocks:
            print("Calculating Relative Strength using bulk download...")
            if self.monitor:
                with self.monitor.monitor_operation("calculate_bulk_rs", {"stock_count": len(stocks)}):
                    rs_results = self._calculate_bulk_rs(stocks)
            else:
                rs_results = self._calculate_bulk_rs(stocks)
            
            # Add RS data to each stock
            for stock in stocks:
                symbol = stock['symbol']
                if symbol in rs_results:
                    stock['relative_strength'] = rs_results[symbol]
                else:
                    stock['relative_strength'] = {'rs_spy': None, 'rs_sector': None}
        
        if self.monitor:
            self.monitor.record_data_processed(len(stocks))
        
        return stocks
    
    def get_performance_summary(self) -> Optional[Dict]:
        """Get performance monitoring summary"""
        if self.monitor:
            return self.monitor.get_session_summary()
        return None
    
    def print_performance_summary(self):
        """Print performance monitoring summary"""
        if self.monitor:
            self.monitor.print_summary()


# Example usage
if __name__ == "__main__":
    stock_data = StockData()
    stocks = stock_data.get_all_stocks()
    
    print("\n=== STOCK DATA ===")
    for stock in stocks:
        print(f"{stock['symbol']}: {stock['company_name']}")
        print(f"  Market Cap: ${stock['market_cap']:,.0f}")
        print(f"  Price: ${stock['price']:.2f}")
        print(f"  Current EPS: ${stock['eps']:.2f}")
        print(f"  Sector: {stock['sector']}")
        
        # Show EPS history
        eps_history = stock.get('eps_history', {})
        if eps_history.get('latest_quarterly_eps'):
            print(f"  Latest Quarterly EPS: ${eps_history['latest_quarterly_eps']:.2f}")
        
        # Show recent quarterly EPS data
        if eps_history.get('quarterly'):
            print("  Recent Quarterly EPS:")
            for quarter, eps in list(eps_history['quarterly'].items())[:4]:  # Show last 4 quarters
                print(f"    {quarter}: ${eps:.2f}")
        
        print()
    
    # Print performance summary
    stock_data.print_performance_summary()
