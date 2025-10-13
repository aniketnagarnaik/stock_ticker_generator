# Data Providers

Extensible data provider system for stock market data.

## Architecture

```
publisher/data_publisher.py
    ↓
data_providers/provider_manager.py
    ↓
    ├─→ data_providers/defeatbeta_provider.py (primary)
    └─→ data_providers/yahoo_provider.py (fallback)
```

## Available Providers

### 1. defeatbeta-api (Primary)
- **Source**: Hugging Face dataset
- **Cost**: Free
- **Rate Limits**: None
- **Works on Render**: ✅ Yes
- **Data Freshness**: Updated daily (last: Oct 10, 2025)
- **Pros**: No rate limits, works everywhere, free
- **Cons**: Data is 1 day old (not real-time)

### 2. Yahoo Finance (Fallback)
- **Source**: Yahoo Finance via yfinance + curl_cffi
- **Cost**: Free
- **Rate Limits**: Yes (blocked on some hosting providers)
- **Works on Render**: ❌ Blocked
- **Data Freshness**: Real-time
- **Pros**: Real-time data, comprehensive
- **Cons**: Rate limiting, IP blocking on cloud hosts

## Configuration

Set provider priority via environment variable:

```bash
# Use defeatbeta first, then Yahoo (default)
export DATA_PROVIDER_PRIORITY="defeatbeta,yahoo"

# Use only Yahoo
export DATA_PROVIDER_PRIORITY="yahoo"

# Use only defeatbeta
export DATA_PROVIDER_PRIORITY="defeatbeta"
```

## Adding New Providers

1. Create `data_providers/your_provider.py`
2. Implement `BaseDataProvider` interface
3. Add to `ProviderManager.__init__()` 
4. Add to priority list

Example:

```python
from data_providers.base_provider import BaseDataProvider

class YourProvider(BaseDataProvider):
    def get_provider_name(self) -> str:
        return "Your Provider Name"
    
    def is_available(self) -> bool:
        # Check if API key exists, etc.
        return True
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        # Fetch and return stock data
        pass
    
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        # Fetch all stocks
        pass
```

## Data Format

All providers must return data in this format:

```python
{
    'symbol': 'AAPL',
    'company_name': 'Apple Inc.',
    'market_cap': 3639902455300,
    'eps': 6.59,
    'price': 245.27,
    'sector': 'Technology',
    'industry': 'Consumer Electronics',
    'eps_history': {
        'quarterly': {
            '2024-09-30': 0.97,
            '2024-12-31': 2.40,
            # ...
        }
    },
    'eps_growth': {
        'quarter_over_quarter': -4.85,
        'year_over_year': 61.86,
        'latest_quarters': [0.97, 2.40, 1.65, 1.57]
    },
    'ema_data': {
        'D_9EMA': 253.29,
        'D_21EMA': 249.71,
        # ...
    },
    'relative_strength': {
        'rs_spy': 4.3,
        'rs_sector': -4.96
    }
}
```

