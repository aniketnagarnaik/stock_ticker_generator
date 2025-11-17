#!/usr/bin/env python3
"""
30-Year Extended Backtesting
Run momentum strategy from 1994-2024 using all available historical data
"""

import sys
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

sys.path.append('..')
sys.path.append('.')

from quarterly_backtesting_engine import QuarterlyBacktestingEngine
from postgres_data_manager import PostgresDataManager

def run_30_year_backtest():
    """Run backtesting from 1994 to 2024"""
    print("🚀 30-YEAR MOMENTUM BACKTESTING (1994-2024)")
    print("=" * 60)
    
    # Initialize components
    start_date = "1994-01-01"
    end_date = "2024-12-31"
    engine = QuarterlyBacktestingEngine(start_date, end_date)
    dm = PostgresDataManager()
    
    # Define test stocks (we'll use all available)
    test_stocks = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA']
    
    # SPY file path
    spy_file_path = "/Users/aniketnagarnaik/Downloads/archive/spy-historical.csv"
    
    print(f"📊 Testing with stocks: {test_stocks}")
    print(f"📈 SPY data from: {spy_file_path}")
    print(f"📅 Period: 1994-2024 (30+ years)")
    print()
    
    # Run the backtest
    try:
        results = engine.run_backtest(top_n=2)
        
        print("\n🎯 30-YEAR BACKTEST RESULTS:")
        print("=" * 50)
        print(f"Initial Capital:        ${100000:>10,.0f}")
        print(f"Final Portfolio Value: ${results['final_portfolio_value']:>10,.0f}")
        print(f"Total Return:          {results['total_return']:>10.2f}%")
        print(f"Annualized Return:     {results['annual_return']:>10.2f}%")
        print(f"Total Quarters:       {len(results['quarterly_returns']):>10}")
        
        # Calculate win rate
        positive_quarters = sum(1 for ret in results['quarterly_returns'] if ret > 0)
        win_rate = (positive_quarters / len(results['quarterly_returns'])) * 100
        print(f"Win Rate:              {win_rate:>10.1f}%")
        
        print(f"Portfolio Volatility:  {results['portfolio_volatility']:>10.2f}%")
        print(f"Sharpe Ratio:          {results['sharpe_ratio']:>10.2f}")
        
        print(f"\n📊 SPY COMPARISON:")
        print(f"SPY Volatility:        {results['spy_volatility']:>10.2f}%")
        print(f"Average Excess Return: {results['average_excess_return']:>10.2f}%")
        print(f"Outperformance Rate:   {results['outperformance_rate']:>10.1f}%")
        
        # Show quarterly breakdown
        print(f"\n📈 QUARTERLY PERFORMANCE BREAKDOWN:")
        print("-" * 60)
        for i, (q_return, spy_return) in enumerate(zip(results['quarterly_returns'], results['spy_returns'])):
            quarter_num = i + 1
            year = 1994 + (quarter_num - 1) // 4
            quarter = ((quarter_num - 1) % 4) + 1
            excess = q_return - spy_return
            print(f"Q{quarter} {year}: {q_return:>8.2f}% vs SPY {spy_return:>6.2f}% (excess: {excess:+6.2f}%)")
        
        # Analyze by decades
        print(f"\n📊 PERFORMANCE BY DECADE:")
        print("-" * 40)
        
        # 1990s (1994-1999)
        nineties_returns = results['quarterly_returns'][:24]  # 6 years * 4 quarters
        nineties_spy = results['spy_returns'][:24]
        nineties_total = sum(nineties_returns)
        nineties_spy_total = sum(nineties_spy)
        print(f"1990s (1994-1999): {nineties_total:>8.2f}% vs SPY {nineties_spy_total:>6.2f}%")
        
        # 2000s (2000-2009)
        thousands_returns = results['quarterly_returns'][24:64]  # 10 years * 4 quarters
        thousands_spy = results['spy_returns'][24:64]
        thousands_total = sum(thousands_returns)
        thousands_spy_total = sum(thousands_spy)
        print(f"2000s (2000-2009): {thousands_total:>8.2f}% vs SPY {thousands_spy_total:>6.2f}%")
        
        # 2010s (2010-2019)
        tens_returns = results['quarterly_returns'][64:104]  # 10 years * 4 quarters
        tens_spy = results['spy_returns'][64:104]
        tens_total = sum(tens_returns)
        tens_spy_total = sum(tens_spy)
        print(f"2010s (2010-2019): {tens_total:>8.2f}% vs SPY {tens_spy_total:>6.2f}%")
        
        # 2020s (2020-2024)
        twenties_returns = results['quarterly_returns'][104:]  # Remaining quarters
        twenties_spy = results['spy_returns'][104:]
        twenties_total = sum(twenties_returns)
        twenties_spy_total = sum(twenties_spy)
        print(f"2020s (2020-2024): {twenties_total:>8.2f}% vs SPY {twenties_spy_total:>6.2f}%")
        
        return results
        
    except Exception as e:
        print(f"❌ Error running 30-year backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    results = run_30_year_backtest()
    
    if results:
        print(f"\n✅ 30-year backtesting completed successfully!")
        print(f"📊 Results show {results['total_return']:.2f}% total return over 30 years")
        print(f"📈 Annualized return: {results['annualized_return']:.2f}%")
    else:
        print(f"\n❌ 30-year backtesting failed")
