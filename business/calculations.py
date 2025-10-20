"""
Business logic for financial calculations (EMA, RS, EPS growth)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta


class FinancialCalculations:
    """Business logic for financial calculations"""
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> float:
        """
        Calculate Exponential Moving Average
        
        Args:
            prices: Series of prices
            period: EMA period
            
        Returns:
            Latest EMA value
        """
        if len(prices) < period:
            return None
        
        ema = prices.ewm(span=period).mean()
        return float(ema.iloc[-1])
    
    @staticmethod
    def calculate_all_emas(price_data: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate all EMA values for different timeframes
        
        Args:
            price_data: DataFrame with 'date' and 'close' columns
            
        Returns:
            Dictionary with EMA values
        """
        if price_data.empty:
            return {}
        
        # Ensure we have close prices
        if 'close' not in price_data.columns:
            return {}
        
        prices = price_data['close']
        
        ema_data = {}
        
        # Daily EMAs
        ema_data['D_9EMA'] = FinancialCalculations.calculate_ema(prices, 9)
        ema_data['D_21EMA'] = FinancialCalculations.calculate_ema(prices, 21)
        ema_data['D_50EMA'] = FinancialCalculations.calculate_ema(prices, 50)
        
        # Weekly EMAs (using every 5th day as weekly approximation)
        if len(prices) >= 45:  # Need at least 9 weeks
            weekly_prices = prices.iloc[::5]  # Every 5th day
            ema_data['W_9EMA'] = FinancialCalculations.calculate_ema(weekly_prices, 9)
            ema_data['W_21EMA'] = FinancialCalculations.calculate_ema(weekly_prices, 21)
            ema_data['W_50EMA'] = FinancialCalculations.calculate_ema(weekly_prices, 50)
        
        # Monthly EMAs (using every 21st day as monthly approximation)
        if len(prices) >= 189:  # Need at least 9 months
            monthly_prices = prices.iloc[::21]  # Every 21st day
            ema_data['M_9EMA'] = FinancialCalculations.calculate_ema(monthly_prices, 9)
            ema_data['M_21EMA'] = FinancialCalculations.calculate_ema(monthly_prices, 21)
        
        # Remove None values
        return {k: v for k, v in ema_data.items() if v is not None}
    
    @staticmethod
    def calculate_relative_strength(stock_prices: pd.DataFrame, 
                                  benchmark_data: Dict[str, pd.DataFrame],
                                  sector: str = None,
                                  sector_etf: str = None) -> Dict[str, float]:
        """
        Calculate relative strength vs benchmarks
        
        Args:
            stock_prices: Stock price DataFrame with 'date' and 'close' columns
            benchmark_data: Dictionary of benchmark DataFrames
            sector: Stock sector (e.g., 'Technology', 'Healthcare')
            sector_etf: Sector ETF symbol (e.g., 'XLK', 'XLV') - if not provided, will be determined from sector
            
        Returns:
            Dictionary with RS values
        """
        if stock_prices.empty or not benchmark_data:
            return {'rs_spy': None, 'rs_sector': None}
        
        try:
            # Prepare stock data
            stock_df = stock_prices.copy()
            stock_df['date'] = pd.to_datetime(stock_df['date'])
            stock_df = stock_df.set_index('date')['close']
            
            rs_values = {}
            
            # Calculate RS vs SPY (primary benchmark)
            if 'SPY' in benchmark_data:
                spy_df = benchmark_data['SPY'].copy()
                spy_df['date'] = pd.to_datetime(spy_df['date'])
                spy_df = spy_df.set_index('date')['close']
                
                rs_spy = FinancialCalculations._calculate_rs_ratio(stock_df, spy_df)
                rs_values['rs_spy'] = rs_spy
            
            # Calculate RS vs sector ETF
            # Determine sector ETF if not provided
            if not sector_etf and sector:
                from business.sector_mapper import SectorMapper
                sector_mapper = SectorMapper()
                sector_etf = sector_mapper.get_sector_etf(sector)
            
            # Calculate RS against sector ETF if available
            if sector_etf and sector_etf in benchmark_data:
                sector_df = benchmark_data[sector_etf].copy()
                sector_df['date'] = pd.to_datetime(sector_df['date'])
                sector_df = sector_df.set_index('date')['close']
                
                rs_sector = FinancialCalculations._calculate_rs_ratio(stock_df, sector_df)
                rs_values['rs_sector'] = rs_sector
            else:
                # Fallback to QQQ if sector ETF not available
                if 'QQQ' in benchmark_data:
                    qqq_df = benchmark_data['QQQ'].copy()
                    qqq_df['date'] = pd.to_datetime(qqq_df['date'])
                    qqq_df = qqq_df.set_index('date')['close']
                    
                    rs_sector = FinancialCalculations._calculate_rs_ratio(stock_df, qqq_df)
                    rs_values['rs_sector'] = rs_sector
                    print(f"  ⚠️ Using QQQ as fallback for sector {sector} (ETF: {sector_etf})", flush=True)
                else:
                    rs_values['rs_sector'] = None
            
            return rs_values
            
        except Exception as e:
            print(f"Error calculating relative strength: {e}", flush=True)
            return {'rs_spy': None, 'rs_sector': None}
    
    @staticmethod
    def _calculate_rs_ratio(stock_prices: pd.Series, benchmark_prices: pd.Series) -> Optional[float]:
        """
        Calculate relative strength ratio between stock and benchmark
        
        Args:
            stock_prices: Stock price series
            benchmark_prices: Benchmark price series
            
        Returns:
            RS ratio or None if calculation fails
        """
        try:
            # Align dates
            common_dates = stock_prices.index.intersection(benchmark_prices.index)
            if len(common_dates) < 2:
                return None
            
            stock_aligned = stock_prices.loc[common_dates]
            benchmark_aligned = benchmark_prices.loc[common_dates]
            
            # Calculate returns
            stock_returns = stock_aligned.pct_change().dropna()
            benchmark_returns = benchmark_aligned.pct_change().dropna()
            
            # Align returns
            common_return_dates = stock_returns.index.intersection(benchmark_returns.index)
            if len(common_return_dates) < 30:  # Need at least 30 days
                return None
            
            stock_returns = stock_returns.loc[common_return_dates]
            benchmark_returns = benchmark_returns.loc[common_return_dates]
            
            # Calculate weighted RS using 3, 6, 9, and 12-month periods
            periods = [63, 126, 189, 252]  # Approximate trading days
            weights = [0.4, 0.3, 0.2, 0.1]  # More weight to recent performance
            
            rs_values = []
            
            for period in periods:
                if len(stock_returns) >= period:
                    stock_period = stock_returns.tail(period)
                    benchmark_period = benchmark_returns.tail(period)
                    
                    # Calculate cumulative returns
                    stock_cumulative = (1 + stock_period).prod() - 1
                    benchmark_cumulative = (1 + benchmark_period).prod() - 1
                    
                    # Calculate RS ratio
                    if benchmark_cumulative != 0:
                        rs_ratio = (stock_cumulative / benchmark_cumulative - 1) * 100
                        rs_values.append(rs_ratio)
            
            if not rs_values:
                return None
            
            # Return weighted average
            return sum(rs * weight for rs, weight in zip(rs_values, weights[:len(rs_values)]))
            
        except Exception as e:
            print(f"Error calculating RS ratio: {e}", flush=True)
            return None
    
    @staticmethod
    def calculate_eps_growth(eps_history: Dict) -> Dict[str, float]:
        """
        Calculate EPS growth metrics
        
        Args:
            eps_history: Dictionary with EPS history data
            
        Returns:
            Dictionary with growth metrics
        """
        try:
            if not eps_history or 'data' not in eps_history:
                return {'qoq': None, 'yoy': None}
            
            eps_data = eps_history['data']
            if len(eps_data) < 2:
                return {'qoq': None, 'yoy': None}
            
            # Sort by date (most recent first)
            eps_data_sorted = sorted(eps_data, key=lambda x: x['date'], reverse=True)
            
            # Quarter over quarter growth
            if len(eps_data_sorted) >= 2:
                latest_eps = eps_data_sorted[0]['eps']
                previous_eps = eps_data_sorted[1]['eps']
                
                if previous_eps != 0:
                    qoq_growth = ((latest_eps - previous_eps) / abs(previous_eps)) * 100
                else:
                    qoq_growth = 0
            else:
                qoq_growth = None
            
            # Year over year growth (4 quarters back)
            if len(eps_data_sorted) >= 5:
                latest_eps = eps_data_sorted[0]['eps']
                year_ago_eps = eps_data_sorted[4]['eps']
                
                if year_ago_eps != 0:
                    yoy_growth = ((latest_eps - year_ago_eps) / abs(year_ago_eps)) * 100
                else:
                    yoy_growth = 0
            else:
                yoy_growth = None
            
            # Get latest 4 quarters for sparkline charts
            latest_quarters = [quarter['eps'] for quarter in eps_data_sorted[:4]]
            latest_quarters.reverse()  # Oldest to newest for chart display
            
            return {
                'qoq': qoq_growth,
                'yoy': yoy_growth,
                'latest_eps': eps_data_sorted[0]['eps'] if eps_data_sorted else None,
                'latest_quarters': latest_quarters
            }
            
        except Exception as e:
            print(f"Error calculating EPS growth: {e}", flush=True)
            return {'qoq': None, 'yoy': None, 'latest_eps': None}
