"""
Provider Manager - Selects and manages data providers with priority and fallback
"""

import os
from typing import List, Dict, Optional
from data_providers.defeatbeta_provider import DefeatBetaProvider
from data_providers.yahoo_provider import YahooProvider


class ProviderManager:
    """Manages multiple data providers with priority and fallback logic"""
    
    def __init__(self):
        # Initialize all available providers
        self.defeatbeta = DefeatBetaProvider()
        self.yahoo = YahooProvider()
        
        # Define provider priority (can be configured via env var)
        self.provider_priority = self._get_provider_priority()
        
        # Log which providers are available
        self._log_provider_status()
    
    def _get_provider_priority(self) -> List[str]:
        """Get provider priority order from environment or use default"""
        # Allow override via environment variable
        priority_env = os.getenv('DATA_PROVIDER_PRIORITY', 'defeatbeta,yahoo')
        priority = [p.strip() for p in priority_env.split(',')]
        
        print(f"📊 Provider priority: {' → '.join(priority)}", flush=True)
        return priority
    
    def _log_provider_status(self):
        """Log status of all providers"""
        print("\n📡 Data Provider Status:", flush=True)
        print(f"   • defeatbeta-api: {'✅ Available' if self.defeatbeta.is_available() else '❌ Not installed'}", flush=True)
        print(f"   • Yahoo Finance: {'✅ Available' if self.yahoo.is_available() else '❌ Not available'}", flush=True)
        print()
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stock info using priority order with fallback"""
        for provider_name in self.provider_priority:
            provider = self._get_provider(provider_name)
            
            if not provider or not provider.is_available():
                continue
            
            try:
                result = provider.get_stock_info(symbol)
                if result:
                    return result
                else:
                    print(f"⚠️ {provider.get_provider_name()} returned no data for {symbol}, trying next provider...", flush=True)
            except Exception as e:
                print(f"❌ {provider.get_provider_name()} error for {symbol}: {e}", flush=True)
                print(f"   Trying next provider...", flush=True)
        
        print(f"❌ All providers failed for {symbol}", flush=True)
        return None
    
    def get_all_stocks(self, use_test_data: bool = False) -> List[Dict]:
        """Get all stocks using priority order with fallback"""
        for provider_name in self.provider_priority:
            provider = self._get_provider(provider_name)
            
            if not provider or not provider.is_available():
                continue
            
            try:
                print(f"📡 Using {provider.get_provider_name()} as data source", flush=True)
                result = provider.get_all_stocks(use_test_data=use_test_data)
                
                if result and len(result) > 0:
                    print(f"✅ {provider.get_provider_name()} returned {len(result)} stocks", flush=True)
                    return result
                else:
                    print(f"⚠️ {provider.get_provider_name()} returned no data, trying next provider...", flush=True)
            except Exception as e:
                print(f"❌ {provider.get_provider_name()} error: {e}", flush=True)
                print(f"   Trying next provider...", flush=True)
        
        print("❌ All providers failed", flush=True)
        return []
    
    def _get_provider(self, provider_name: str):
        """Get provider instance by name"""
        providers = {
            'defeatbeta': self.defeatbeta,
            'yahoo': self.yahoo,
            'yahoo_finance': self.yahoo,
        }
        return providers.get(provider_name.lower())
    
    def get_active_provider_name(self) -> str:
        """Get the name of the currently active (first available) provider"""
        for provider_name in self.provider_priority:
            provider = self._get_provider(provider_name)
            if provider and provider.is_available():
                return provider.get_provider_name()
        return "No provider available"

