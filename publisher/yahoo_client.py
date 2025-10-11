"""
Yahoo Finance API client for fetching stock data
"""

import yfinance as yf
import time
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class YahooFinanceClient:
    """Client for fetching data from Yahoo Finance API"""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_delay = 3.0  # Rate limiting for 503 stocks - increased to avoid Yahoo Finance limits
        
        # Sector to ETF mapping
        self.sector_etf_map = {
            "Industrials": "XLI",
            "Health Care": "XLV", 
            "Healthcare": "XLV",
            "Technology": "XLK",
            "Utilities": "XLU",
            "Financials": "XLF",
            "Financial Services": "XLF",
            "Materials": "XLB",
            "Consumer Discretionary": "XLY",
            "Consumer Cyclical": "XLY",
            "Real Estate": "XLRE",
            "Communication Services": "XLC",
            "Consumer Staples": "XLP",
            "Consumer Defensive": "XLP",
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
    
    def _get_historical_eps(self, ticker) -> Dict:
        """Get historical EPS data (quarterly only)"""
        try:
            eps_data = {
                'quarterly': {},
                'latest_quarterly_eps': None
            }
            
            # Get quarterly EPS data
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
                
                # Calculate quarter-over-quarter growth
                if len(eps_values) >= 2:
                    current_eps = eps_values[0]
                    previous_eps = eps_values[1]
                    if previous_eps != 0:
                        growth_data['quarter_over_quarter'] = ((current_eps - previous_eps) / abs(previous_eps)) * 100
                
                # Calculate year-over-year growth
                if len(eps_values) >= 4:
                    current_eps = eps_values[0]
                    year_ago_eps = eps_values[3]
                    if year_ago_eps != 0:
                        growth_data['year_over_year'] = ((current_eps - year_ago_eps) / abs(year_ago_eps)) * 100
                
                # Store last 4 quarters
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
        """Calculate all EMAs for a symbol"""
        try:
            # Single download for all timeframes
            data = yf.download(symbol, period="1y", interval="1d", progress=False)
            if data.empty:
                return self._get_empty_ema_dict()
            
            daily_closes = data['Close']
            
            # Calculate daily EMAs
            d_9_ema = self._calculate_ema(daily_closes, 9)
            d_21_ema = self._calculate_ema(daily_closes, 21)
            d_50_ema = self._calculate_ema(daily_closes, 50)
            
            # Resample to weekly (Friday close)
            weekly_data = daily_closes.resample('W-FRI').last().dropna()
            
            # Calculate weekly EMAs
            w_9_ema = self._calculate_ema(weekly_data, 9) if len(weekly_data) >= 9 else None
            w_21_ema = self._calculate_ema(weekly_data, 21) if len(weekly_data) >= 21 else None
            w_50_ema = self._calculate_ema(weekly_data, 50) if len(weekly_data) >= 50 else None
            
            # Resample to monthly
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
        """Bulk download price data for multiple symbols"""
        try:
            print(f"Bulk downloading price data for {len(symbols)} symbols...")
            self._rate_limit()
            
            # Use yfinance bulk download
            data = yf.download(symbols, period="1y", interval="1d", threads=True, progress=False)
            
            result = {}
            for symbol in symbols:
                if symbol in data.columns.levels[1]:
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
        target_date = datetime.now().date() - timedelta(days=months * 30)
        
        # Find price closest to or before the target date
        past_price = None
        for price_data in reversed(prices):
            if price_data['date'] <= target_date:
                past_price = price_data['close']
                break
        
        if past_price is None:
            past_price = prices[0]['close']
        
        if past_price == 0:
            return None
            
        return ((today_price - past_price) / past_price) * 100
    
    def _get_unique_sectors_and_etfs(self, stocks_data: List[Dict]) -> List[str]:
        """Get unique sector ETFs needed"""
        etfs = ['SPY']
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
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get basic stock information for a symbol"""
        try:
            self._rate_limit()
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get current price
            hist = ticker.history(period="1d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else 0
            
            # Calculate market cap
            market_cap = info.get('marketCap', 0)
            if market_cap == 0 and 'sharesOutstanding' in info:
                market_cap = current_price * info['sharesOutstanding']
            
            # Get historical EPS data
            eps_data = self._get_historical_eps(ticker)
            
            # Calculate EPS growth
            eps_growth = self._calculate_eps_growth(eps_data)
            
            # Calculate all EMAs
            ema_data = self._calculate_all_emas(symbol)
            
            # Calculate relative strength
            relative_strength = self._calculate_single_stock_rs(symbol)
            
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
                'relative_strength': relative_strength
            }
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
            return None
    
    def _calculate_single_stock_rs(self, symbol: str) -> Dict:
        """Calculate relative strength for a single stock"""
        try:
            # Get price data for the stock
            price_data = yf.download([symbol, 'SPY'], period="2y", interval="1d", progress=False)
            
            # Check if we have data for the symbol
            symbol_close_col = ('Close', symbol)
            spy_close_col = ('Close', 'SPY')
            
            if symbol_close_col not in price_data.columns or price_data[symbol_close_col].empty:
                return {'rs_spy': None, 'rs_sector': None}
            
            # Get sector ETF
            ticker = yf.Ticker(symbol)
            info = ticker.info
            sector = info.get('sector', 'Unknown')
            sector_etf = self.sector_etf_map.get(sector, 'SPY')
            
            # Get sector ETF data if different from SPY
            sector_data = None
            sector_close_col = None
            if sector_etf != 'SPY':
                sector_data = yf.download([sector_etf], period="2y", interval="1d", progress=False)
                if not sector_data.empty:
                    sector_close_col = ('Close', sector_etf)
                else:
                    sector_etf = 'SPY'
            
            # Calculate RS using the same weights as in the original method
            weights = {3: 0.25, 6: 0.25, 9: 0.25, 12: 0.25}
            rs_spy = 0
            rs_sector = 0
            
            stock_prices = price_data[symbol_close_col].dropna()
            spy_prices = price_data[spy_close_col].dropna()
            
            for months, weight in weights.items():
                # Calculate price change for stock
                if len(stock_prices) < months * 21:  # Approximate trading days
                    continue
                
                current_price = stock_prices.iloc[-1]
                old_price = stock_prices.iloc[-(months * 21)]
                ticker_change = ((current_price - old_price) / old_price) * 100
                
                # Calculate SPY change
                if len(spy_prices) >= months * 21:
                    current_spy = spy_prices.iloc[-1]
                    old_spy = spy_prices.iloc[-(months * 21)]
                    spy_change = ((current_spy - old_spy) / old_spy) * 100
                    rs_spy += (ticker_change - spy_change) * weight
                
                # Calculate sector change
                if sector_etf != 'SPY' and sector_close_col and sector_close_col in sector_data.columns:
                    sector_prices = sector_data[sector_close_col].dropna()
                    if len(sector_prices) >= months * 21:
                        current_sector = sector_prices.iloc[-1]
                        old_sector = sector_prices.iloc[-(months * 21)]
                        sector_change = ((current_sector - old_sector) / old_sector) * 100
                        rs_sector += (ticker_change - sector_change) * weight
                else:
                    rs_sector = rs_spy
            
            return {
                'rs_spy': round(rs_spy, 2) if rs_spy != 0 else None,
                'rs_sector': round(rs_sector, 2) if rs_sector != 0 else None
            }
            
        except Exception as e:
            print(f"Error calculating RS for {symbol}: {e}")
            return {'rs_spy': None, 'rs_sector': None}
    
    def load_symbols(self, filename: str = 'data/stock_symbols.txt') -> List[str]:
        """Load stock symbols from file"""
        try:
            with open(filename, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(symbols)} stock symbols")
            return symbols
        except Exception as e:
            print(f"Error loading symbols: {e}")
            return []
    
    def get_all_stocks(self, use_test_data=False) -> List[Dict]:
        """Get all stocks data with efficient bulk RS calculation"""
        if use_test_data:
            symbols = self.load_symbols('data/stock_symbols_test.txt')
        else:
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
            rs_results = self._calculate_bulk_rs(stocks)
            
            # Add RS data to each stock
            for stock in stocks:
                symbol = stock['symbol']
                if symbol in rs_results:
                    stock['relative_strength'] = rs_results[symbol]
                else:
                    stock['relative_strength'] = {'rs_spy': None, 'rs_sector': None}
        
        return stocks
