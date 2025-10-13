"""
Base Data Provider Interface
All data providers must implement this interface for plug-and-play functionality
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class BaseDataProvider(ABC):
    """Abstract base class for all data providers"""
    
    @abstractmethod
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """
        Get complete stock information for a single symbol
        
        Returns dict with keys:
        - symbol: str
        - company_name: str
        - market_cap: int
        - eps: float
        - price: float
        - sector: str
        - industry: str
        - eps_history: dict with 'quarterly' key containing {date: eps_value}
        - eps_growth: dict with 'quarter_over_quarter', 'year_over_year', 'latest_quarters'
        - ema_data: dict with 'D_9EMA', 'D_21EMA', 'D_50EMA', 'W_9EMA', 'W_21EMA', 'W_50EMA', 'M_9EMA', 'M_21EMA'
        - relative_strength: dict with 'rs_spy', 'rs_sector'
        """
        pass
    
    @abstractmethod
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        """
        Get data for all stocks
        
        Args:
            use_test_data: If True, use test symbols file instead of full list
            
        Returns:
            List of stock info dicts (same format as get_stock_info)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this provider is available/configured
        
        Returns:
            True if provider can be used, False otherwise
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of this provider
        
        Returns:
            Provider name (e.g., 'Yahoo Finance', 'defeatbeta-api')
        """
        pass
    
    def get_data_snapshot_date(self) -> Optional[str]:
        """
        Get the latest data snapshot date from the provider
        
        Returns:
            Date string in YYYY-MM-DD format, or None if not available
        """
        return None
    
    def load_symbols(self, file_path: str = 'data/stock_symbols.txt') -> List[str]:
        """
        Load stock symbols from file (common implementation for all providers)
        
        Args:
            file_path: Path to symbols file
            
        Returns:
            List of stock symbols
        """
        try:
            with open(file_path, 'r') as f:
                symbols = [line.strip() for line in f if line.strip()]
            print(f"Loaded {len(symbols)} stock symbols from {file_path}", flush=True)
            return symbols
        except Exception as e:
            print(f"Error loading symbols from {file_path}: {e}", flush=True)
            return []

