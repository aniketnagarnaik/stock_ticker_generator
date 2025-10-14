"""
defeatbeta-api Data Provider (Refactored)
Uses Hugging Face dataset - only fetches raw data, no business logic
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
    """Data provider using defeatbeta-api (Hugging Face dataset) - Raw data only"""
    
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
        """Get raw stock information from defeatbeta-api"""
        if not self.is_available():
            return None
        
        try:
            # Rate limiting
            import time
            time.sleep(self.request_delay)
            
            print(f"  📊 Fetching {symbol} from defeatbeta-api (Hugging Face)...", flush=True)
            
            # Initialize ticker
            ticker = DefeatBetaTicker(symbol)
            
            # Get company info
            info = ticker.info()
            if info.empty:
                print(f"    ❌ {symbol}: No company info available", flush=True)
                return None
            
            info_row = info.iloc[0]
            
            # Get current price
            price_df = ticker.price()
            if price_df.empty:
                print(f"    ❌ {symbol}: No price data available", flush=True)
                return None
            
            latest_price_row = price_df.iloc[-1]
            current_price = latest_price_row['close']
            
            # Get market cap
            try:
                market_cap_df = ticker.market_capitalization()
                market_cap = int(market_cap_df.iloc[-1]['market_capitalization']) if not market_cap_df.empty else 0
            except:
                market_cap = 0
            
            # Get EPS data (raw)
            eps_data = self._get_raw_eps_data(ticker)
            
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
            
            # Return raw data - business logic will be handled by DataOrchestrator
            return {
                'symbol': symbol,
                'company_name': company_name,
                'market_cap': int(market_cap) if market_cap else 0,
                'price': float(current_price),
                'sector': str(info_row.get('sector', 'Unknown')),
                'industry': str(info_row.get('industry', 'Unknown')),
                'price_data': price_df,
                'eps_history': eps_data
            }
            
        except Exception as e:
            print(f"    ❌ {symbol}: Error fetching data - {e}", flush=True)
            return None
    
    def _get_raw_eps_data(self, ticker) -> Dict:
        """Extract raw EPS history from defeatbeta ticker"""
        try:
            ttm_eps = ticker.ttm_eps()
            
            if ttm_eps.empty:
                return {'data': []}
            
            # Convert to list of dictionaries with date and eps
            eps_data = []
            for idx, row in ttm_eps.iterrows():
                eps_data.append({
                    'date': str(row['report_date']),
                    'eps': float(row['eps'])
                })
            
            return {'data': eps_data}
            
        except Exception as e:
            print(f"Error getting raw EPS data: {e}", flush=True)
            return {'data': []}
    
    def get_all_stocks(self, symbols: List[str]) -> List[Dict]:
        """Get raw data for multiple stocks"""
        if not self.is_available():
            return []
        
        results = []
        for symbol in symbols:
            stock_data = self.get_stock_info(symbol)
            if stock_data:
                results.append(stock_data)
        
        return results
