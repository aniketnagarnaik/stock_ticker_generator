"""
Stock Data Fetcher - Yahoo Finance Integration
Clean and focused implementation
"""

import yfinance as yf
import time
from typing import List, Dict, Optional


class StockData:
    """Stock data fetcher using Yahoo Finance"""
    
    def __init__(self):
        self.last_request_time = 0
        self.request_delay = 0.5  # Rate limiting
    
    def _rate_limit(self):
        """Simple rate limiting to avoid overwhelming Yahoo Finance"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
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
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'market_cap': market_cap,
                'eps': info.get('trailingEps', 0),
                'price': current_price,
                'sector': info.get('sector', 'Unknown')
            }
            
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
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
        """Get all stocks data"""
        symbols = self.load_symbols()
        stocks = []
        
        print(f"Fetching data for {len(symbols)} stocks...")
        
        for symbol in symbols:
            print(f"Processing: {symbol}")
            
            stock_info = self.get_stock_info(symbol)
            if stock_info:
                stocks.append(stock_info)
                print(f"  ✅ {symbol}: {stock_info['company_name']} - Market Cap: ${stock_info['market_cap']:,.0f}")
            else:
                print(f"  ❌ {symbol}: Failed to get data")
        
        print(f"Successfully loaded {len(stocks)} stocks")
        return stocks


# Example usage
if __name__ == "__main__":
    stock_data = StockData()
    stocks = stock_data.get_all_stocks()
    
    print("\n=== STOCK DATA ===")
    for stock in stocks:
        print(f"{stock['symbol']}: {stock['company_name']}")
        print(f"  Market Cap: ${stock['market_cap']:,.0f}")
        print(f"  Price: ${stock['price']:.2f}")
        print(f"  EPS: ${stock['eps']:.2f}")
        print(f"  Sector: {stock['sector']}")
        print()
