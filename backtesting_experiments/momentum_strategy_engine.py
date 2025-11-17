#!/usr/bin/env python3
"""
Modular Strategy Layer for Momentum Trading System
Core logic for calculating momentum scores and signals
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

sys.path.append('..')
from postgres_data_manager import PostgresDataManager

class MomentumStrategyEngine:
    """Core momentum strategy calculation engine"""
    
    def __init__(self, data_manager: PostgresDataManager):
        self.dm = data_manager
        print("⚙️ MomentumStrategyEngine initialized")
    
    def calculate_rs_vs_spy(self, symbol: str, end_date: str, periods: List[int] = None) -> float:
        """Calculate Relative Strength vs SPY - FIXED VERSION"""
        if periods is None:
            periods = [63, 126, 189, 252]  # ~3, 6, 9, 12 months
        
        try:
            # Get stock and SPY data - use a wider date range to ensure we have enough data
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=500)).strftime('%Y-%m-%d')
            
            stock_data = self.dm.get_stock_prices(symbol, start_date, end_date)
            spy_data = self.dm.get_spy_data(start_date, end_date)
            
            if stock_data.empty or spy_data.empty:
                print(f"  ⚠️ Missing data for RS calculation: stock={len(stock_data)}, spy={len(spy_data)}")
                return 0.0
            
            # Align data by date
            stock_data = stock_data.set_index('date')
            spy_data = spy_data.set_index('date')
            
            # Convert to float to avoid decimal issues
            stock_data['close'] = stock_data['close'].astype(float)
            spy_data['close'] = spy_data['close'].astype(float)
            
            combined_data = pd.concat([stock_data['close'], spy_data['close']], axis=1, join='inner')
            combined_data.columns = ['stock', 'spy']
            
            if len(combined_data) < 63:  # Need at least 63 days for shortest period
                print(f"  ⚠️ Not enough combined data for RS calculation: {len(combined_data)} records")
                return 0.0
            
            # Calculate returns
            stock_returns = combined_data['stock'].pct_change().dropna()
            spy_returns = combined_data['spy'].pct_change().dropna()
            
            rs_values = []
            weights = [0.4, 0.3, 0.2, 0.1]  # Weighted towards shorter periods
            
            for i, period in enumerate(periods):
                if len(stock_returns) >= period and len(spy_returns) >= period:
                    stock_period = stock_returns.tail(period)
                    spy_period = spy_returns.tail(period)
                    
                    # Calculate cumulative returns
                    stock_cumulative = (1 + stock_period).prod() - 1
                    spy_cumulative = (1 + spy_period).prod() - 1
                    
                    if abs(spy_cumulative) > 0.001:  # Safety check
                        # FIXED: Calculate RS as (Stock Return - SPY Return) * 100
                        # This gives positive values when stock outperforms SPY
                        rs_ratio = (stock_cumulative - spy_cumulative) * 100
                        rs_ratio = max(-1000, min(1000, rs_ratio))  # Cap extreme values
                        weighted_rs = rs_ratio * weights[i]
                        rs_values.append(weighted_rs)
                        print(f"    Period {period}d: Stock={stock_cumulative:.2%}, SPY={spy_cumulative:.2%}, RS={rs_ratio:.2f}%, Weighted={weighted_rs:.2f}")
                    else:
                        print(f"    Period {period}d: SPY cumulative too small ({spy_cumulative:.6f})")
                        rs_values.append(0)
                else:
                    print(f"    Period {period}d: Not enough data (have {len(stock_returns)})")
                    rs_values.append(0)
            
            total_rs = sum(rs_values) if rs_values else 0.0
            print(f"    Total RS: {total_rs:.2f}")
            return total_rs
            
        except Exception as e:
            print(f"❌ Error calculating RS vs SPY for {symbol}: {e}")
            return 0.0
    
    def calculate_eps_momentum(self, symbol: str, end_date: str) -> float:
        """Calculate EPS momentum score - positive for growing EPS"""
        try:
            # Get EPS data for last 4 quarters
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=400)).strftime('%Y-%m-%d')
            eps_data = self.dm.get_stock_eps(symbol, start_date, end_date)
            
            if eps_data.empty or len(eps_data) < 2:
                return 0.0
            
            # Get latest EPS values
            latest_eps = eps_data.tail(min(4, len(eps_data)))['eps'].values
            
            if len(latest_eps) < 2:
                return 0.0
            
            # Convert to float to avoid decimal issues
            latest_eps = [float(x) for x in latest_eps]
            
            # Calculate EPS growth rate (momentum)
            if len(latest_eps) >= 2:
                # Simple growth rate: (latest - previous) / previous
                eps_growth = (latest_eps[-1] - latest_eps[-2]) / abs(latest_eps[-2]) if latest_eps[-2] != 0 else 0
                momentum_score = eps_growth * 100
            else:
                momentum_score = 0
            
            return max(-100, min(100, momentum_score))  # Cap between -100% and +100%
            
        except Exception as e:
            print(f"❌ Error calculating EPS momentum for {symbol}: {e}")
            return 0.0
    
    def calculate_price_momentum(self, symbol: str, end_date: str) -> float:
        """Calculate price momentum score"""
        try:
            # Get price data for multiple periods
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=400)).strftime('%Y-%m-%d')
            price_data = self.dm.get_stock_prices(symbol, start_date, end_date)
            
            if price_data.empty:
                return 0.0
            
            price_data = price_data.set_index('date')
            current_price = float(price_data['close'].iloc[-1])
            
            # Calculate momentum over different periods
            periods = [21, 63, 126]  # 1, 3, 6 months
            weights = [0.5, 0.3, 0.2]
            
            momentum_values = []
            for i, period in enumerate(periods):
                if len(price_data) >= period:
                    past_price = float(price_data['close'].iloc[-period])
                    period_return = (current_price - past_price) / past_price * 100
                    momentum_values.append(period_return * weights[i])
                else:
                    momentum_values.append(0)
            
            return sum(momentum_values) if momentum_values else 0.0
            
        except Exception as e:
            print(f"❌ Error calculating price momentum for {symbol}: {e}")
            return 0.0
    
    def calculate_pe_momentum(self, symbol: str, end_date: str) -> float:
        """Calculate P/E ratio momentum score - positive for increasing P/E (momentum)"""
        try:
            # Get P/E data
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=400)).strftime('%Y-%m-%d')
            pe_data = self.dm.get_stock_pe_ratios(symbol, start_date, end_date)
            
            if pe_data.empty or len(pe_data) < 2:
                return 0.0
            
            pe_data = pe_data.set_index('date')
            
            # Calculate P/E trend (increasing P/E is momentum, decreasing is value)
            recent_pe = float(pe_data['pe'].iloc[-1])
            older_pe = float(pe_data['pe'].iloc[-min(21, len(pe_data)-1)])  # 1 month ago
            
            if older_pe == 0:
                return 0.0
            
            # Positive momentum is good (P/E increasing - momentum)
            pe_momentum = (recent_pe - older_pe) / older_pe * 100
            return max(-100, min(100, pe_momentum))
            
        except Exception as e:
            print(f"❌ Error calculating P/E momentum for {symbol}: {e}")
            return 0.0
    
    def calculate_volume_momentum(self, symbol: str, end_date: str) -> float:
        """Calculate volume momentum score"""
        try:
            # Get volume data
            start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=400)).strftime('%Y-%m-%d')
            price_data = self.dm.get_stock_prices(symbol, start_date, end_date)
            
            if price_data.empty or len(price_data) < 21:
                return 0.0
            
            price_data = price_data.set_index('date')
            
            # Calculate average volume over different periods
            recent_volume = float(price_data['volume'].tail(5).mean())  # Last 5 days
            older_volume = float(price_data['volume'].tail(21).mean())   # Last 21 days
            
            if older_volume == 0:
                return 0.0
            
            # Higher volume is generally positive
            volume_momentum = (recent_volume - older_volume) / older_volume * 100
            return max(-100, min(100, volume_momentum))
            
        except Exception as e:
            print(f"❌ Error calculating volume momentum for {symbol}: {e}")
            return 0.0
    
    def calculate_combined_score(self, symbol: str, end_date: str) -> Dict[str, float]:
        """Calculate all momentum scores for a symbol with adaptive weighting"""
        print(f"📊 Calculating momentum scores for {symbol}...")
        
        scores = {
            'rs_vs_spy': self.calculate_rs_vs_spy(symbol, end_date),
            'eps_momentum': self.calculate_eps_momentum(symbol, end_date),
            'price_momentum': self.calculate_price_momentum(symbol, end_date),
            'pe_momentum': self.calculate_pe_momentum(symbol, end_date),
            'volume_momentum': self.calculate_volume_momentum(symbol, end_date)
        }
        
        # Base weights
        base_weights = {
            'rs_vs_spy': 0.35,      # Most important - relative strength
            'eps_momentum': 0.25,    # Fundamental momentum
            'price_momentum': 0.20, # Technical momentum
            'pe_momentum': 0.10,     # Value momentum
            'volume_momentum': 0.10  # Volume confirmation
        }
        
        # Adaptive weighting: adjust weights based on data availability
        available_scores = {k: v for k, v in scores.items() if v != 0.0}
        unavailable_scores = {k: v for k, v in scores.items() if v == 0.0}
        
        if unavailable_scores:
            print(f"  ⚠️ Missing data for {symbol}: {list(unavailable_scores.keys())}")
            
            # Redistribute weights from unavailable scores to available ones
            total_unavailable_weight = sum(base_weights[k] for k in unavailable_scores.keys())
            total_available_weight = sum(base_weights[k] for k in available_scores.keys())
            
            if total_available_weight > 0:
                # Redistribute proportionally
                redistribution_factor = total_unavailable_weight / total_available_weight
                adaptive_weights = {}
                
                for score_type in base_weights.keys():
                    if score_type in available_scores:
                        # Increase weight for available scores
                        adaptive_weights[score_type] = base_weights[score_type] * (1 + redistribution_factor)
                    else:
                        # Set weight to 0 for unavailable scores
                        adaptive_weights[score_type] = 0.0
                
                # Normalize weights to sum to 1.0
                total_weight = sum(adaptive_weights.values())
                if total_weight > 0:
                    adaptive_weights = {k: v / total_weight for k, v in adaptive_weights.items()}
                
                print(f"  📊 Adaptive weights: {adaptive_weights}")
                weights = adaptive_weights
            else:
                weights = base_weights
        else:
            weights = base_weights
        
        # Convert all scores to float to avoid decimal/float issues
        combined_score = sum(float(scores[key]) * weights[key] for key in scores.keys())
        scores['combined_score'] = combined_score
        
        print(f"  📈 {symbol}: RS={scores['rs_vs_spy']:.2f}, EPS={scores['eps_momentum']:.2f}, "
              f"Price={scores['price_momentum']:.2f}, P/E={scores['pe_momentum']:.2f}, "
              f"Volume={scores['volume_momentum']:.2f}, Combined={combined_score:.2f}")
        
        return scores
    
    def calculate_scores_for_symbols(self, symbols: List[str], end_date: str) -> Dict[str, Dict]:
        """Calculate momentum scores for multiple symbols"""
        print(f"🚀 Calculating momentum scores for {len(symbols)} symbols...")
        
        all_scores = {}
        for symbol in symbols:
            try:
                scores = self.calculate_combined_score(symbol, end_date)
                all_scores[symbol] = scores
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                all_scores[symbol] = {
                    'rs_vs_spy': 0.0,
                    'eps_momentum': 0.0,
                    'price_momentum': 0.0,
                    'pe_momentum': 0.0,
                    'volume_momentum': 0.0,
                    'combined_score': 0.0
                }
        
        # Rank symbols by combined score
        sorted_symbols = sorted(all_scores.items(), key=lambda x: x[1]['combined_score'], reverse=True)
        
        for rank, (symbol, scores) in enumerate(sorted_symbols, 1):
            scores['rank'] = rank
        
        print(f"✅ Calculated scores for {len(all_scores)} symbols")
        return all_scores
    
    def get_top_stocks(self, symbols: List[str], end_date: str, top_n: int = 5) -> List[str]:
        """Get top N stocks by momentum score"""
        scores = self.calculate_scores_for_symbols(symbols, end_date)
        
        # Sort by combined score and return top N
        sorted_symbols = sorted(scores.items(), key=lambda x: x[1]['combined_score'], reverse=True)
        return [symbol for symbol, _ in sorted_symbols[:top_n]]
    
    def get_momentum_signals(self, symbol: str, end_date: str) -> Dict[str, str]:
        """Get momentum signals for a symbol"""
        scores = self.calculate_combined_score(symbol, end_date)
        
        signals = {}
        
        # RS vs SPY signal
        if scores['rs_vs_spy'] > 10:
            signals['rs_signal'] = 'STRONG'
        elif scores['rs_vs_spy'] > 5:
            signals['rs_signal'] = 'POSITIVE'
        elif scores['rs_vs_spy'] < -10:
            signals['rs_signal'] = 'WEAK'
        elif scores['rs_vs_spy'] < -5:
            signals['rs_signal'] = 'NEGATIVE'
        else:
            signals['rs_signal'] = 'NEUTRAL'
        
        # EPS momentum signal
        if scores['eps_momentum'] > 5:
            signals['eps_signal'] = 'ACCELERATING'
        elif scores['eps_momentum'] > 0:
            signals['eps_signal'] = 'POSITIVE'
        elif scores['eps_momentum'] < -5:
            signals['eps_signal'] = 'DECELERATING'
        elif scores['eps_momentum'] < 0:
            signals['eps_signal'] = 'NEGATIVE'
        else:
            signals['eps_signal'] = 'STABLE'
        
        # Price momentum signal
        if scores['price_momentum'] > 10:
            signals['price_signal'] = 'STRONG_UPTREND'
        elif scores['price_momentum'] > 5:
            signals['price_signal'] = 'UPTREND'
        elif scores['price_momentum'] < -10:
            signals['price_signal'] = 'STRONG_DOWNTREND'
        elif scores['price_momentum'] < -5:
            signals['price_signal'] = 'DOWNTREND'
        else:
            signals['price_signal'] = 'SIDEWAYS'
        
        # Overall signal
        if scores['combined_score'] > 15:
            signals['overall'] = 'STRONG_BUY'
        elif scores['combined_score'] > 5:
            signals['overall'] = 'BUY'
        elif scores['combined_score'] < -15:
            signals['overall'] = 'STRONG_SELL'
        elif scores['combined_score'] < -5:
            signals['overall'] = 'SELL'
        else:
            signals['overall'] = 'HOLD'
        
        return signals

if __name__ == "__main__":
    # Test the strategy engine
    print("🧪 Testing MomentumStrategyEngine...")
    
    from postgres_data_manager import PostgresDataManager
    
    dm = PostgresDataManager()
    engine = MomentumStrategyEngine(dm)
    
    # Test with available symbols
    symbols = dm.get_available_symbols()
    if symbols:
        test_symbols = symbols[:3]  # Test with first 3 symbols
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📊 Testing with symbols: {test_symbols}")
        scores = engine.calculate_scores_for_symbols(test_symbols, end_date)
        
        print("\n📈 Results:")
        for symbol, score_data in scores.items():
            print(f"  {symbol}: Combined Score = {score_data['combined_score']:.2f}")
    
    print("✅ MomentumStrategyEngine test complete!")
