#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quarterly Momentum Backtesting Engine
500 stocks → top 5 selection with quarterly rebalancing
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

sys.path.append('..')
from postgres_data_manager import PostgresDataManager
from momentum_strategy_engine import MomentumStrategyEngine
from sqlalchemy import text

class PortfolioManager:
    """Manages portfolio positions and transactions"""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {symbol: shares}
        self.portfolio_value = initial_capital
        self.transaction_history = []
        self.portfolio_history = []
        
    def get_current_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value"""
        total_value = self.cash
        
        for symbol, shares in self.positions.items():
            if symbol in current_prices:
                total_value += shares * current_prices[symbol]
        
        return total_value
    
    def rebalance_portfolio(self, target_stocks: List[str], current_prices: Dict[str, float], 
                          transaction_cost: float = 0.001) -> Dict[str, float]:
        """Rebalance portfolio to target stocks with equal weights"""
        
        # Get current portfolio value before rebalancing
        current_portfolio_value = self.get_current_value(current_prices)
        
        # Calculate target value per stock (equal weight)
        target_value_per_stock = current_portfolio_value / len(target_stocks)
        
        # Sell existing positions
        total_sale_proceeds = 0
        for symbol, shares in self.positions.items():
            if symbol in current_prices and shares > 0:
                sale_value = shares * current_prices[symbol]
                sale_cost = sale_value * transaction_cost
                net_proceeds = sale_value - sale_cost
                total_sale_proceeds += net_proceeds
                
                self.transaction_history.append({
                    'date': datetime.now(),
                    'symbol': symbol,
                    'action': 'SELL',
                    'shares': shares,
                    'price': current_prices[symbol],
                    'value': sale_value,
                    'cost': sale_cost,
                    'net_value': net_proceeds
                })
        
        # Clear positions
        self.positions = {}
        
        # Calculate available cash for purchasing (cash + sale proceeds)
        available_cash = self.cash + total_sale_proceeds
        
        # Buy target stocks
        total_purchase_cost = 0
        for symbol in target_stocks:
            if symbol in current_prices:
                target_shares = target_value_per_stock / current_prices[symbol]
                purchase_value = target_shares * current_prices[symbol]
                purchase_cost = purchase_value * transaction_cost
                total_cost = purchase_value + purchase_cost
                
                # Use available cash instead of just sale proceeds
                if total_cost <= available_cash:
                    self.positions[symbol] = target_shares
                    total_purchase_cost += total_cost
                    
                    self.transaction_history.append({
                        'date': datetime.now(),
                        'symbol': symbol,
                        'action': 'BUY',
                        'shares': target_shares,
                        'price': current_prices[symbol],
                        'value': purchase_value,
                        'cost': purchase_cost,
                        'net_value': purchase_value
                    })
        
        # Update cash
        self.cash = available_cash - total_purchase_cost
        
        # Calculate new portfolio value
        new_portfolio_value = self.get_current_value(current_prices)
        self.portfolio_value = new_portfolio_value
        
        return {
            'total_sale_proceeds': total_sale_proceeds,
            'total_purchase_cost': total_purchase_cost,
            'transaction_costs': total_sale_proceeds * transaction_cost + total_purchase_cost * transaction_cost,
            'new_portfolio_value': new_portfolio_value
        }

class QuarterlyBacktestingEngine:
    """Quarterly momentum backtesting engine for 500-stock universe"""
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        self.dm = PostgresDataManager()
        self.strategy_engine = MomentumStrategyEngine(self.dm)
        self.portfolio = PortfolioManager(initial_capital)
        
        print("🚀 QuarterlyBacktestingEngine initialized")
        print(f"📅 Period: {start_date} to {end_date}")
        print(f"💰 Initial Capital: ${initial_capital:,.2f}")
    
    def get_quarterly_dates(self) -> List[Tuple[str, str]]:
        """Get quarterly rebalancing dates"""
        start_dt = datetime.strptime(self.start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        quarterly_dates = []
        current_date = start_dt
        
        while current_date <= end_dt:
            # Calculate quarter end
            quarter_end = current_date + timedelta(days=90)  # ~3 months
            if quarter_end > end_dt:
                quarter_end = end_dt
            
            quarterly_dates.append((
                current_date.strftime('%Y-%m-%d'),
                quarter_end.strftime('%Y-%m-%d')
            ))
            
            current_date = quarter_end + timedelta(days=1)
        
        print(f"📅 Generated {len(quarterly_dates)} quarterly periods")
        return quarterly_dates
    
    def get_available_stocks(self, date: str) -> List[str]:
        """Get stocks with data available on given date"""
        session = self.dm._get_session()
        try:
            result = session.execute(text('''
                SELECT DISTINCT symbol 
                FROM stock_prices 
                WHERE price_date <= :date
                ORDER BY symbol
            '''), {'date': date})
            
            symbols = [row[0] for row in result.fetchall()]
            return symbols
        finally:
            session.close()
    
    def get_stock_prices_on_date(self, symbols: List[str], date: str) -> Dict[str, float]:
        """Get stock prices on a specific date"""
        prices = {}
        
        for symbol in symbols:
            try:
                # Get price data around the date
                start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=5)).strftime('%Y-%m-%d')
                end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=5)).strftime('%Y-%m-%d')
                
                price_data = self.dm.get_stock_prices(symbol, start_date, end_date)
                
                if not price_data.empty:
                    # Find closest date to target date
                    price_data['date'] = pd.to_datetime(price_data['date'])
                    target_date = pd.to_datetime(date)
                    
                    # Get closest price
                    closest_idx = (price_data['date'] - target_date).abs().idxmin()
                    prices[symbol] = float(price_data.loc[closest_idx, 'close'])
                
            except Exception as e:
                print(f"  ⚠️ Error getting price for {symbol} on {date}: {e}")
        
        return prices
    
    def calculate_quarterly_return(self, start_date: str, end_date: str, start_value: float) -> float:
        """Calculate quarterly portfolio return based on portfolio value changes"""
        # Get portfolio value at end of quarter (after holding period)
        end_value = self.portfolio.get_current_value(
            self.get_stock_prices_on_date(list(self.portfolio.positions.keys()), end_date)
        )
        
        if start_value > 0:
            return float((end_value - start_value) / start_value)
        return 0.0
    
    def calculate_spy_quarterly_return(self, start_date: str, end_date: str) -> float:
        """Calculate SPY quarterly return"""
        try:
            spy_data = self.dm.get_spy_data(start_date, end_date)
            
            if not spy_data.empty:
                spy_data['date'] = pd.to_datetime(spy_data['date'])
                spy_data = spy_data.sort_values('date')
                
                start_price = spy_data['close'].iloc[0]
                end_price = spy_data['close'].iloc[-1]
                
                return float((end_price - start_price) / start_price)
            
        except Exception as e:
            print(f"⚠️ Error calculating SPY return: {e}")
        
        return 0.0
    
    def run_backtest(self, top_n: int = 5) -> Dict:
        """Run the quarterly backtesting"""
        print("🚀 Starting Quarterly Momentum Backtesting")
        print("=" * 80)
        
        quarterly_dates = self.get_quarterly_dates()
        quarterly_returns = []
        spy_returns = []
        portfolio_values = []
        rebalancing_log = []
        
        for i, (quarter_start, quarter_end) in enumerate(quarterly_dates):
            print(f"\n📅 Quarter {i+1}/{len(quarterly_dates)}: {quarter_start} to {quarter_end}")
            print("-" * 60)
            
            # Store portfolio value BEFORE rebalancing for return calculation
            portfolio_value_before_rebalancing = self.portfolio.portfolio_value
            
            # Get available stocks
            available_stocks = self.get_available_stocks(quarter_start)
            print(f"📊 Available stocks: {len(available_stocks)}")
            
            if len(available_stocks) < top_n:
                print(f"⚠️ Not enough stocks available ({len(available_stocks)} < {top_n})")
                continue
            
            # Calculate momentum scores for available stocks
            print("⚙️ Calculating momentum scores...")
            scores = self.strategy_engine.calculate_scores_for_symbols(available_stocks, quarter_start)
            
            # Select top N stocks
            sorted_stocks = sorted(scores.items(), key=lambda x: x[1]['combined_score'], reverse=True)
            top_stocks = [symbol for symbol, _ in sorted_stocks[:top_n]]
            
            print(f"🏆 Top {top_n} stocks:")
            for j, (symbol, score_data) in enumerate(sorted_stocks[:top_n]):
                print(f"  {j+1}. {symbol}: {score_data['combined_score']:.2f}")
            
            # Get current prices
            current_prices = self.get_stock_prices_on_date(top_stocks, quarter_start)
            
            if len(current_prices) < top_n:
                print(f"⚠️ Not enough price data ({len(current_prices)} < {top_n})")
                continue
            
            # Rebalance portfolio
            print("🔄 Rebalancing portfolio...")
            rebalance_info = self.portfolio.rebalance_portfolio(top_stocks, current_prices)
            
            print(f"💰 Portfolio Value: ${self.portfolio.portfolio_value:,.2f}")
            print(f"💸 Transaction Costs: ${rebalance_info['transaction_costs']:,.2f}")
            
            # Calculate quarterly returns based on portfolio value changes
            portfolio_return = self.calculate_quarterly_return(quarter_start, quarter_end, portfolio_value_before_rebalancing)
            spy_return = self.calculate_spy_quarterly_return(quarter_start, quarter_end)
            
            quarterly_returns.append(portfolio_return)
            spy_returns.append(spy_return)
            portfolio_values.append(self.portfolio.portfolio_value)
            
            rebalancing_log.append({
                'quarter': i+1,
                'start_date': quarter_start,
                'end_date': quarter_end,
                'top_stocks': top_stocks,
                'portfolio_return': portfolio_return,
                'spy_return': spy_return,
                'excess_return': portfolio_return - spy_return,
                'portfolio_value': self.portfolio.portfolio_value,
                'transaction_costs': rebalance_info['transaction_costs']
            })
            
            print(f"📈 Portfolio Return: {portfolio_return:.2%}")
            print(f"📊 SPY Return: {spy_return:.2%}")
            print(f"🎯 Excess Return: {portfolio_return - spy_return:.2%}")
        
        # Calculate final metrics
        if quarterly_returns:
            total_return = (self.portfolio.portfolio_value - self.initial_capital) / self.initial_capital
            annual_return = (1 + total_return) ** (4 / len(quarterly_returns)) - 1  # Annualized
            
            excess_returns = [p - s for p, s in zip(quarterly_returns, spy_returns)]
            outperformance_rate = sum(1 for x in excess_returns if x > 0) / len(excess_returns)
            
            portfolio_vol = np.std(quarterly_returns) * np.sqrt(4)  # Annualized
            spy_vol = np.std(spy_returns) * np.sqrt(4)  # Annualized
            
            sharpe_ratio = annual_return / portfolio_vol if portfolio_vol > 0 else 0
            
            results = {
                'total_return': total_return,
                'annual_return': annual_return,
                'outperformance_rate': outperformance_rate,
                'average_excess_return': np.mean(excess_returns),
                'portfolio_volatility': portfolio_vol,
                'spy_volatility': spy_vol,
                'sharpe_ratio': sharpe_ratio,
                'quarterly_returns': quarterly_returns,
                'spy_returns': spy_returns,
                'excess_returns': excess_returns,
                'portfolio_values': portfolio_values,
                'rebalancing_log': rebalancing_log,
                'final_portfolio_value': self.portfolio.portfolio_value
            }
            
            return results
        else:
            return {'error': 'No quarterly periods processed'}
    
    def print_results(self, results: Dict):
        """Print backtesting results"""
        if 'error' in results:
            print(f"❌ {results['error']}")
            return
        
        print("\n" + "=" * 80)
        print("📊 BACKTESTING RESULTS")
        print("=" * 80)
        
        print(f"💰 Final Portfolio Value: ${results['final_portfolio_value']:,.2f}")
        print(f"📈 Total Return: {results['total_return']:.2%}")
        print(f"📊 Annual Return: {results['annual_return']:.2%}")
        print(f"🎯 Outperformance Rate: {results['outperformance_rate']:.1%}")
        print(f"📊 Average Excess Return: {results['average_excess_return']:.2%}")
        print(f"📈 Portfolio Volatility: {results['portfolio_volatility']:.2%}")
        print(f"📊 SPY Volatility: {results['spy_volatility']:.2%}")
        print(f"⚡ Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        
        print(f"\n📅 Quarterly Performance Summary:")
        print(f"  Quarters: {len(results['quarterly_returns'])}")
        print(f"  Positive Quarters: {sum(1 for r in results['quarterly_returns'] if r > 0)}")
        print(f"  Negative Quarters: {sum(1 for r in results['quarterly_returns'] if r < 0)}")
        
        print(f"\n🏆 Top Performing Quarters:")
        for i, (q_return, spy_return) in enumerate(zip(results['quarterly_returns'], results['spy_returns'])):
            excess = q_return - spy_return
            if excess > 0.05:  # >5% outperformance
                print(f"  Quarter {i+1}: {q_return:.1%} vs SPY {spy_return:.1%} (+{excess:.1%})")

if __name__ == "__main__":
    print("🚀 Quarterly Momentum Backtesting Engine")
    print("=" * 80)
    
    # Initialize backtesting engine
    engine = QuarterlyBacktestingEngine(
        start_date='2020-01-01',
        end_date='2025-10-24',
        initial_capital=100000
    )
    
    # Run backtest
    results = engine.run_backtest(top_n=5)
    
    # Print results
    engine.print_results(results)
    
    print("\n✅ Quarterly backtesting complete!")
