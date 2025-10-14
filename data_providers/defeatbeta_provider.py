"""
defeatbeta-api Data Provider
Uses Hugging Face dataset (no rate limits, works on Render)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime
from data_providers.base_provider import BaseDataProvider

try:
    from defeatbeta_api.data.ticker import Ticker as DefeatBetaTicker
    DEFEATBETA_AVAILABLE = True
except ImportError:
    DEFEATBETA_AVAILABLE = False
    print("⚠️ defeatbeta-api not installed. Install with: pip install defeatbeta-api", flush=True)


class DefeatBetaProvider(BaseDataProvider):
    """Data provider using defeatbeta-api (Hugging Face dataset)"""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_delay = 0.5  # Small delay to be polite
    
    def is_available(self) -> bool:
        """Check if defeatbeta-api is installed"""
        return DEFEATBETA_AVAILABLE
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "defeatbeta-api (Hugging Face)"
    
    def get_data_snapshot_date(self) -> Optional[str]:
        """Get the latest data snapshot date from the dataset"""
        if not self.is_available():
            return None
        
        try:
            # Use AAPL as a reference to get the latest data date
            ticker = DefeatBetaTicker('AAPL')
            price_df = ticker.price()
            
            if not price_df.empty:
                latest_date = price_df.iloc[-1]['report_date']
                return str(latest_date)
            return None
        except Exception as e:
            print(f"Error getting data snapshot date: {e}", flush=True)
            return None
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get complete stock information for a single symbol"""
        if not self.is_available():
            return None
        
        try:
            ticker = DefeatBetaTicker(symbol)
            
            # Get company info
            info = ticker.info()
            if info.empty:
                print(f"❌ No info for {symbol}", flush=True)
                return None
            
            info_row = info.iloc[0]
            
            # Get current price
            price_df = ticker.price()
            if price_df.empty:
                print(f"❌ No price data for {symbol}", flush=True)
                return None
            
            latest_price_row = price_df.iloc[-1]
            current_price = latest_price_row['close']
            
            # Get market cap
            try:
                market_cap_df = ticker.market_capitalization()
                market_cap = int(market_cap_df.iloc[-1]['market_capitalization']) if not market_cap_df.empty else 0
            except:
                market_cap = 0
            
            # Get EPS data
            eps_data = self._get_eps_data(ticker)
            
            # Calculate EMAs from price history
            ema_data = self._calculate_emas(price_df)
            
            # Calculate relative strength
            relative_strength = self._calculate_rs(symbol, price_df)
            
            # Extract company name from business summary or use symbol as fallback
            business_summary = info_row.get('long_business_summary', '')
            if business_summary and 'Inc.' in business_summary:
                # Extract company name from business summary (usually starts with company name)
                company_name = business_summary.split(' designs,')[0].split(' manufactures,')[0].split(' Inc.')[0] + ' Inc.'
            elif business_summary and 'Corporation' in business_summary:
                company_name = business_summary.split(' designs,')[0].split(' manufactures,')[0].split(' Corporation')[0] + ' Corporation'
            elif business_summary and 'LLC' in business_summary:
                company_name = business_summary.split(' designs,')[0].split(' manufactures,')[0].split(' LLC')[0] + ' LLC'
            else:
                # Fallback to symbol if we can't extract company name
                company_name = symbol
            
            # Convert all numpy types to Python native types for PostgreSQL
            return {
                'symbol': symbol,
                'company_name': company_name,
                'market_cap': int(market_cap) if market_cap else 0,
                'eps': float(eps_data.get('latest_eps', 0)),
                'price': float(current_price),
                'sector': str(info_row.get('sector', 'Unknown')),
                'industry': str(info_row.get('industry', 'Unknown')),
                'eps_history': eps_data.get('eps_history', {}),
                'eps_growth': eps_data.get('eps_growth', {}),
                'ema_data': {k: (float(v) if v is not None else None) for k, v in ema_data.items()},
                'relative_strength': {k: (float(v) if v is not None else None) for k, v in relative_strength.items()}
            }
            
        except Exception as e:
            print(f"Error getting defeatbeta data for {symbol}: {e}", flush=True)
            return None
    
    def _get_eps_data(self, ticker) -> Dict:
        """Extract EPS history and growth from defeatbeta ticker"""
        try:
            ttm_eps = ticker.ttm_eps()
            
            if ttm_eps.empty:
                return {
                    'latest_eps': 0,
                    'eps_history': {'quarterly': {}},
                    'eps_growth': {'quarter_over_quarter': None, 'year_over_year': None, 'latest_quarters': []}
                }
            
            # Build quarterly EPS dictionary (all quarters)
            quarterly_eps = {}
            for idx, row in ttm_eps.iterrows():
                date_str = str(row['report_date'])
                eps_value = float(row['eps'])
                quarterly_eps[date_str] = eps_value
            
            # Get latest quarters (last 4)
            latest_quarters = ttm_eps.tail(4)['eps'].tolist()
            
            # Calculate growth
            qoq_growth = None
            yoy_growth = None
            
            if len(ttm_eps) >= 2:
                current_eps = ttm_eps.iloc[-1]['eps']
                prev_quarter_eps = ttm_eps.iloc[-2]['eps']
                if prev_quarter_eps != 0:
                    qoq_growth = ((current_eps - prev_quarter_eps) / abs(prev_quarter_eps)) * 100
            
            if len(ttm_eps) >= 5:
                current_eps = ttm_eps.iloc[-1]['eps']
                yoy_eps = ttm_eps.iloc[-5]['eps']  # 4 quarters ago
                if yoy_eps != 0:
                    yoy_growth = ((current_eps - yoy_eps) / abs(yoy_eps)) * 100
            
            return {
                'latest_eps': float(ttm_eps.iloc[-1]['tailing_eps']) if 'tailing_eps' in ttm_eps.columns else float(ttm_eps.iloc[-1]['eps']),
                'eps_history': {'quarterly': {k: float(v) for k, v in quarterly_eps.items()}},
                'eps_growth': {
                    'quarter_over_quarter': float(qoq_growth) if qoq_growth is not None else None,
                    'year_over_year': float(yoy_growth) if yoy_growth is not None else None,
                    'latest_quarters': [float(x) for x in latest_quarters]
                }
            }
            
        except Exception as e:
            print(f"Error getting EPS data: {e}", flush=True)
            return {
                'latest_eps': 0,
                'eps_history': {'quarterly': {}},
                'eps_growth': {'quarter_over_quarter': None, 'year_over_year': None, 'latest_quarters': []}
            }
    
    def _calculate_emas(self, price_df: pd.DataFrame) -> Dict:
        """Calculate EMAs from price history"""
        try:
            closes = price_df['close']
            
            # Daily EMAs
            d_9ema = self._calc_single_ema(closes, 9)
            d_21ema = self._calc_single_ema(closes, 21)
            d_50ema = self._calc_single_ema(closes, 50)
            
            # Weekly EMAs (resample)
            price_df_copy = price_df.copy()
            price_df_copy['date'] = pd.to_datetime(price_df_copy['report_date'])
            price_df_copy.set_index('date', inplace=True)
            weekly_closes = price_df_copy['close'].resample('W').last().dropna()
            
            w_9ema = self._calc_single_ema(weekly_closes, 9)
            w_21ema = self._calc_single_ema(weekly_closes, 21)
            w_50ema = self._calc_single_ema(weekly_closes, 50)
            
            # Monthly EMAs
            monthly_closes = price_df_copy['close'].resample('ME').last().dropna()
            m_9ema = self._calc_single_ema(monthly_closes, 9)
            m_21ema = self._calc_single_ema(monthly_closes, 21)
            
            return {
                'D_9EMA': d_9ema,
                'D_21EMA': d_21ema,
                'D_50EMA': d_50ema,
                'W_9EMA': w_9ema,
                'W_21EMA': w_21ema,
                'W_50EMA': w_50ema,
                'M_9EMA': m_9ema,
                'M_21EMA': m_21ema
            }
            
        except Exception as e:
            print(f"Error calculating EMAs: {e}", flush=True)
            return {}
    
    def _calc_single_ema(self, prices: pd.Series, period: int) -> Optional[float]:
        """Calculate single EMA"""
        try:
            if len(prices) < period:
                return None
            ema = prices.ewm(span=period, adjust=False).mean()
            return float(ema.iloc[-1])
        except:
            return None
    
    def _calculate_rs(self, symbol: str, price_df: pd.DataFrame) -> Dict:
        """Calculate relative strength vs SPY using database benchmark data"""
        try:
            print(f"  📊 Calculating real RS for {symbol} using database benchmarks...", flush=True)
            
            # Get benchmark data from database
            from database.indices_manager import indices_manager
            
            benchmark_data = indices_manager.get_all_indices_data()
            
            if benchmark_data:
                # Prepare stock price data for RS calculation
                stock_prices = price_df[['report_date', 'close']].copy()
                stock_prices.columns = ['date', 'close']
                
                # Calculate real relative strength using Polygon provider's method
                from .polygon_provider import PolygonProvider
                polygon_provider = PolygonProvider()
                rs_values = polygon_provider.calculate_relative_strength(stock_prices, benchmark_data)
                
                print(f"    ✅ {symbol} RS vs SPY: {rs_values.get('rs_spy', 'N/A')}", flush=True)
                print(f"    ✅ {symbol} RS vs Sector: {rs_values.get('rs_sector', 'N/A')}", flush=True)
                
                return rs_values
            else:
                print(f"    ⚠️ No benchmark data available in database", flush=True)
            
            # No fallback - return None if no real benchmark data available
            print(f"  ⚠️ No real benchmark data available for {symbol}, returning N/A", flush=True)
            return {'rs_spy': None, 'rs_sector': None}
            
        except Exception as e:
            print(f"Error calculating RS for {symbol}: {e}", flush=True)
            return {'rs_spy': None, 'rs_sector': None}
    
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        """Get all stocks data"""
        if use_test_data:
            symbols = self.load_symbols('data/stock_symbols_test.txt')
        else:
            symbols = self.load_symbols()
        
        stocks = []
        
        print(f"Fetching data for {len(symbols)} stocks from {self.get_provider_name()}...", flush=True)
        
        for symbol in symbols:
            print(f"Processing: {symbol}", flush=True)
            
            stock_info = self.get_stock_info(symbol)
            
            if stock_info:
                stocks.append(stock_info)
                print(f"  ✅ {symbol}: Data fetched", flush=True)
            else:
                print(f"  ❌ {symbol}: Failed to get data", flush=True)
        
        print(f"Successfully loaded {len(stocks)} stocks from {self.get_provider_name()}", flush=True)
        return stocks

