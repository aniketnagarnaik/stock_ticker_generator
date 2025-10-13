"""
Yahoo Finance Data Provider
Wraps the existing yahoo_client for the provider interface
"""

from typing import List, Dict, Optional
from data_providers.base_provider import BaseDataProvider
from publisher.yahoo_client import YahooFinanceClient


class YahooProvider(BaseDataProvider):
    """Data provider using Yahoo Finance (with curl_cffi)"""
    
    def __init__(self):
        self.client = YahooFinanceClient()
    
    def is_available(self) -> bool:
        """Yahoo Finance is always available"""
        return True
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return "Yahoo Finance"
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stock info from Yahoo Finance"""
        return self.client.get_stock_info(symbol)
    
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        """Get all stocks from Yahoo Finance"""
        return self.client.get_all_stocks(use_test_data=use_test_data)

