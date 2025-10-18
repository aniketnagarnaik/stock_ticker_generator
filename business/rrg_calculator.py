"""
RRG (Relative Rotation Graph) Calculator
========================================

Calculates RS-Ratio and RS-Momentum for sector ETFs using 4-week momentum approach.

Formula:
- RS-Ratio = (ETF_Price / SPY_Price) * 100
- RS-Momentum = (Current_RS - RS_4weeks_ago) / RS_4weeks_ago * 100

Quadrants:
- Leading (Top Right): Strong RS + Strong Momentum
- Weakening (Bottom Right): Strong RS + Weak Momentum  
- Lagging (Bottom Left): Weak RS + Weak Momentum
- Improving (Top Left): Weak RS + Strong Momentum
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json


class RRGCalculator:
    """Calculate RRG data for sector ETFs"""
    
    def __init__(self):
        self.sector_etfs = [
            'SPY', 'QQQ',  # Benchmarks
            'XLK', 'XLV', 'XLF', 'XLY', 'XLP', 'XLE', 
            'XLI', 'XLB', 'XLRE', 'XLU', 'XLC'  # Sector ETFs
        ]
    
    def calculate_rrg_data(self, indices_data: List[Dict]) -> List[Dict]:
        """
        Calculate RRG data for all ETFs
        
        Args:
            indices_data: List of index data from database
            
        Returns:
            List of RRG data for each ETF
        """
        rrg_data = []
        
        # Get SPY data for RS-Ratio calculations
        spy_data = self._get_etf_data(indices_data, 'SPY')
        if not spy_data:
            print("❌ SPY data not found - cannot calculate RRG")
            return []
        
        # Calculate RRG for each ETF
        for etf_symbol in self.sector_etfs:
            if etf_symbol == 'SPY':
                continue  # Skip SPY (it's the benchmark)
                
            etf_data = self._get_etf_data(indices_data, etf_symbol)
            if not etf_data:
                print(f"⚠️ {etf_symbol} data not found - skipping")
                continue
            
            rrg_point = self._calculate_single_rrg(etf_symbol, etf_data, spy_data)
            if rrg_point:
                rrg_data.append(rrg_point)
        
        return rrg_data
    
    def _get_etf_data(self, indices_data: List[Dict], symbol: str) -> Optional[Dict]:
        """Get ETF data from indices_data"""
        for index in indices_data:
            if index.get('symbol') == symbol:
                return index
        return None
    
    def _calculate_single_rrg(self, etf_symbol: str, etf_data: Dict, spy_data: Dict) -> Optional[Dict]:
        """
        Calculate RRG data for a single ETF
        
        Args:
            etf_symbol: ETF symbol (e.g., 'XLK')
            etf_data: ETF price data
            spy_data: SPY price data
            
        Returns:
            RRG data dictionary
        """
        try:
            # Parse price data
            etf_prices = self._parse_price_data(etf_data.get('price_data'))
            spy_prices = self._parse_price_data(spy_data.get('price_data'))
            
            if not etf_prices or not spy_prices:
                return None
            
            # Get weekly data (every 5 days = 1 week)
            etf_weekly = self._get_weekly_closes(etf_prices)
            spy_weekly = self._get_weekly_closes(spy_prices)
            
            if len(etf_weekly) < 5 or len(spy_weekly) < 5:  # Need at least 5 weeks
                return None
            
            # Calculate current RS-Ratio
            current_rs = (etf_weekly[0] / spy_weekly[0]) * 100
            
            # Calculate RS-Momentum (4-week)
            if len(etf_weekly) >= 5:  # Need at least 5 weeks of data
                rs_4weeks_ago = (etf_weekly[4] / spy_weekly[4]) * 100
                rs_momentum = (current_rs - rs_4weeks_ago) / rs_4weeks_ago * 100
            else:
                rs_momentum = 0.0
            
            # Determine quadrant
            quadrant = self._determine_quadrant(current_rs, rs_momentum)
            
            return {
                'symbol': etf_symbol,
                'name': self._get_etf_name(etf_symbol),
                'rs_ratio': round(current_rs, 2),
                'rs_momentum': round(rs_momentum, 2),
                'quadrant': quadrant,
                'current_price': etf_weekly[0],
                'spy_price': spy_weekly[0],
                'calculated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error calculating RRG for {etf_symbol}: {e}")
            return None
    
    def _parse_price_data(self, price_data_json: str) -> List[Dict]:
        """Parse price data from JSON string"""
        try:
            if isinstance(price_data_json, str):
                data = json.loads(price_data_json)
            else:
                data = price_data_json
            
            if 'data' in data:
                return data['data']
            return []
        except:
            return []
    
    def _get_weekly_closes(self, daily_prices: List[Dict]) -> List[float]:
        """Extract weekly closing prices from daily data"""
        weekly_closes = []
        
        # Take every 5th day (approximately weekly)
        for i in range(0, len(daily_prices), 5):
            if i < len(daily_prices):
                weekly_closes.append(float(daily_prices[i].get('close', 0)))
        
        return weekly_closes
    
    def _determine_quadrant(self, rs_ratio: float, rs_momentum: float) -> str:
        """Determine RRG quadrant based on RS-Ratio and RS-Momentum"""
        if rs_ratio >= 100 and rs_momentum >= 0:
            return "Leading"
        elif rs_ratio >= 100 and rs_momentum < 0:
            return "Weakening"
        elif rs_ratio < 100 and rs_momentum < 0:
            return "Lagging"
        else:  # rs_ratio < 100 and rs_momentum >= 0
            return "Improving"
    
    def _get_etf_name(self, symbol: str) -> str:
        """Get display name for ETF"""
        names = {
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ ETF',
            'XLK': 'Technology',
            'XLV': 'Healthcare',
            'XLF': 'Financial Services',
            'XLY': 'Consumer Discretionary',
            'XLP': 'Consumer Staples',
            'XLE': 'Energy',
            'XLI': 'Industrials',
            'XLB': 'Materials',
            'XLRE': 'Real Estate',
            'XLU': 'Utilities',
            'XLC': 'Communication Services'
        }
        return names.get(symbol, symbol)
    
    def get_quadrant_summary(self, rrg_data: List[Dict]) -> Dict:
        """Get summary of ETFs in each quadrant"""
        summary = {
            'Leading': [],
            'Weakening': [],
            'Lagging': [],
            'Improving': []
        }
        
        for etf in rrg_data:
            quadrant = etf.get('quadrant', 'Unknown')
            if quadrant in summary:
                summary[quadrant].append(etf)
        
        return summary
