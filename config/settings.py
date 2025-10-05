"""
Configuration Settings for Stock Data Viewer
============================================

This module contains all configuration settings for the application,
including API settings, cache configuration, and deployment settings.

Author: Stock Data Viewer Team
Last Updated: October 2025
"""

import os
from typing import Dict, Any

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = False
    TESTING = False
    
    # Server Configuration
    HOST = '0.0.0.0'
    PORT = int(os.environ.get('PORT', 5000))
    
    # Cache Configuration
    CACHE_EXPIRY_HOURS = 24
    CACHE_FILE = 'stock_cache.json'
    CACHE_METADATA_FILE = 'cache_metadata.json'
    
    # API Configuration
    YAHOO_FINANCE_RATE_LIMIT = 1.0  # seconds between requests
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    # Data Configuration
    STOCK_SYMBOLS_FILE = 'stock_symbols.txt'
    SP500_COMPANIES_FILE = 'sp500_companies.json'
    
    # Performance Configuration
    ENABLE_MONITORING = True
    MEMORY_THRESHOLD_MB = 100
    
    # Sector ETF Mapping
    SECTOR_ETF_MAP = {
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
    
    # EMA Configuration
    EMA_PERIODS = {
        'daily': [9, 21, 50],
        'weekly': [9, 21, 50],
        'monthly': [9, 21]
    }
    
    # Relative Strength Configuration
    RS_PERIODS = [3, 6, 9]  # months
    RS_WEIGHTS = [0.5, 0.3, 0.2]  # weights for 3, 6, 9 month periods
    
    # Market Configuration
    BENCHMARK_ETF = 'SPY'
    TIMEZONE = 'US/Pacific'
    
    @staticmethod
    def get_cache_config() -> Dict[str, Any]:
        """Get cache configuration dictionary"""
        return {
            'expiry_hours': Config.CACHE_EXPIRY_HOURS,
            'cache_file': Config.CACHE_FILE,
            'metadata_file': Config.CACHE_METADATA_FILE
        }
    
    @staticmethod
    def get_api_config() -> Dict[str, Any]:
        """Get API configuration dictionary"""
        return {
            'rate_limit': Config.YAHOO_FINANCE_RATE_LIMIT,
            'max_retries': Config.MAX_RETRIES,
            'retry_delay': Config.RETRY_DELAY
        }
    
    @staticmethod
    def get_performance_config() -> Dict[str, Any]:
        """Get performance configuration dictionary"""
        return {
            'enable_monitoring': Config.ENABLE_MONITORING,
            'memory_threshold_mb': Config.MEMORY_THRESHOLD_MB
        }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENABLE_MONITORING = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENABLE_MONITORING = False  # Disable in production for performance

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    ENABLE_MONITORING = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: str = None) -> Config:
    """
    Get configuration class based on environment
    
    Args:
        config_name: Configuration name (development, production, testing)
        
    Returns:
        Configuration class instance
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return config.get(config_name, DevelopmentConfig)
