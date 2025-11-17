#!/usr/bin/env python3
"""
Specific Tests for Tech Stock Performance Verification
Test that our tech stocks actually performed well in 2020-2024
"""

import unittest
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append('..')
sys.path.append('.')

from postgres_data_manager import PostgresDataManager

class TestTechStockPerformance(unittest.TestCase):
    """Test that tech stocks actually performed well"""
    
    def setUp(self):
        self.dm = PostgresDataManager()
        self.tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    def test_individual_stock_performance_2020(self):
        """Test individual stock performance in 2020"""
        print("\n📈 INDIVIDUAL STOCK PERFORMANCE 2020:")
        print("-" * 50)
        
        for symbol in self.tech_stocks:
            with self.subTest(symbol=symbol):
                price_data = self.dm.get_stock_prices(symbol, '2020-01-01', '2020-12-31')
                
                if not price_data.empty and len(price_data) > 1:
                    start_price = price_data['close'].iloc[0]
                    end_price = price_data['close'].iloc[-1]
                    annual_return = (end_price - start_price) / start_price
                    
                    print(f"{symbol:6s}: {annual_return:8.2%} ({start_price:8.2f} → {end_price:8.2f})")
                    
                    # All tech stocks should have positive returns in 2020
                    self.assertGreater(annual_return, 0, 
                                    f"{symbol} should have positive return in 2020")
    
    def test_individual_stock_performance_2021(self):
        """Test individual stock performance in 2021"""
        print("\n📈 INDIVIDUAL STOCK PERFORMANCE 2021:")
        print("-" * 50)
        
        for symbol in self.tech_stocks:
            with self.subTest(symbol=symbol):
                price_data = self.dm.get_stock_prices(symbol, '2021-01-01', '2021-12-31')
                
                if not price_data.empty and len(price_data) > 1:
                    start_price = price_data['close'].iloc[0]
                    end_price = price_data['close'].iloc[-1]
                    annual_return = (end_price - start_price) / start_price
                    
                    print(f"{symbol:6s}: {annual_return:8.2%} ({start_price:8.2f} → {end_price:8.2f})")
    
    def test_individual_stock_performance_2022(self):
        """Test individual stock performance in 2022"""
        print("\n📈 INDIVIDUAL STOCK PERFORMANCE 2022:")
        print("-" * 50)
        
        for symbol in self.tech_stocks:
            with self.subTest(symbol=symbol):
                price_data = self.dm.get_stock_prices(symbol, '2022-01-01', '2022-12-31')
                
                if not price_data.empty and len(price_data) > 1:
                    start_price = price_data['close'].iloc[0]
                    end_price = price_data['close'].iloc[-1]
                    annual_return = (end_price - start_price) / start_price
                    
                    print(f"{symbol:6s}: {annual_return:8.2%} ({start_price:8.2f} → {end_price:8.2f})")
    
    def test_cumulative_performance_2020_2024(self):
        """Test cumulative performance from 2020 to 2024"""
        print("\n📈 CUMULATIVE PERFORMANCE 2020-2024:")
        print("-" * 50)
        
        for symbol in self.tech_stocks:
            with self.subTest(symbol=symbol):
                price_data = self.dm.get_stock_prices(symbol, '2020-01-01', '2024-12-31')
                
                if not price_data.empty and len(price_data) > 1:
                    start_price = price_data['close'].iloc[0]
                    end_price = price_data['close'].iloc[-1]
                    total_return = (end_price - start_price) / start_price
                    
                    print(f"{symbol:6s}: {total_return:8.2%} ({start_price:8.2f} → {end_price:8.2f})")
                    
                    # Most tech stocks should have positive cumulative returns
                    if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
                        self.assertGreater(total_return, 0, 
                                         f"{symbol} should have positive cumulative return")
    
    def test_quarterly_performance_analysis(self):
        """Analyze quarterly performance to understand the issue"""
        print("\n📊 QUARTERLY PERFORMANCE ANALYSIS:")
        print("-" * 50)
        
        for symbol in self.tech_stocks:
            print(f"\n{symbol}:")
            price_data = self.dm.get_stock_prices(symbol, '2020-01-01', '2024-12-31')
            
            if not price_data.empty:
                # Calculate quarterly returns
                price_data['date'] = pd.to_datetime(price_data['date'])
                price_data = price_data.set_index('date')
                
                # Convert to float to avoid decimal issues
                quarterly_returns = quarterly_returns.astype(float)
                
                print(f"  Average quarterly return: {quarterly_returns.mean():.2%}")
                print(f"  Volatility (std): {quarterly_returns.std():.2%}")
                print(f"  Positive quarters: {(quarterly_returns > 0).sum()}/{len(quarterly_returns)}")
                
                # Show worst quarters
                worst_quarters = quarterly_returns.nsmallest(3)
                print(f"  Worst quarters: {worst_quarters.values}")
    
    def test_spy_performance_comparison(self):
        """Compare tech stocks to SPY performance"""
        print("\n📊 SPY COMPARISON:")
        print("-" * 50)
        
        # Get SPY data
        spy_data = self.dm.get_spy_data('2020-01-01', '2024-12-31')
        
        if not spy_data.empty:
            spy_start = spy_data['close'].iloc[0]
            spy_end = spy_data['close'].iloc[-1]
            spy_return = (spy_end - spy_start) / spy_start
            
            print(f"SPY: {spy_return:8.2%} ({spy_start:8.2f} → {spy_end:8.2f})")
            
            # Compare each tech stock to SPY
            for symbol in self.tech_stocks:
                price_data = self.dm.get_stock_prices(symbol, '2020-01-01', '2024-12-31')
                
                if not price_data.empty and len(price_data) > 1:
                    start_price = price_data['close'].iloc[0]
                    end_price = price_data['close'].iloc[-1]
                    stock_return = (end_price - start_price) / start_price
                    
                    excess_return = stock_return - spy_return
                    print(f"{symbol:6s}: {stock_return:8.2%} (vs SPY: {excess_return:+8.2%})")

class TestPortfolioSimulation(unittest.TestCase):
    """Test portfolio simulation with real data"""
    
    def setUp(self):
        self.dm = PostgresDataManager()
    
    def test_simple_buy_and_hold_strategy(self):
        """Test simple buy and hold strategy with tech stocks"""
        print("\n💰 BUY AND HOLD STRATEGY TEST:")
        print("-" * 50)
        
        # Simulate buying equal amounts of tech stocks in 2020
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        initial_capital = 100000.0
        amount_per_stock = initial_capital / len(symbols)
        
        print(f"Initial capital: ${initial_capital:,.2f}")
        print(f"Amount per stock: ${amount_per_stock:,.2f}")
        
        # Get prices at start and end
        start_prices = {}
        end_prices = {}
        
        for symbol in symbols:
            start_data = self.dm.get_stock_prices(symbol, '2020-01-01', '2020-01-01')
            end_data = self.dm.get_stock_prices(symbol, '2024-12-31', '2024-12-31')
            
            if not start_data.empty and not end_data.empty:
                start_prices[symbol] = start_data['close'].iloc[0]
                end_prices[symbol] = end_data['close'].iloc[-1]
        
        if len(start_prices) == len(symbols):
            # Calculate final portfolio value
            final_value = 0
            for symbol in symbols:
                shares = amount_per_stock / start_prices[symbol]
                final_value += shares * end_prices[symbol]
            
            total_return = (final_value - initial_capital) / initial_capital
            
            print(f"Final portfolio value: ${final_value:,.2f}")
            print(f"Total return: {total_return:.2%}")
            
            # This should be positive for tech stocks
            self.assertGreater(total_return, 0, 
                             "Buy and hold tech stocks should be profitable")
    
    def test_quarterly_rebalancing_simulation(self):
        """Simulate quarterly rebalancing with real data"""
        print("\n🔄 QUARTERLY REBALANCING SIMULATION:")
        print("-" * 50)
        
        # Define quarterly dates
        quarters = [
            ('2020-01-01', '2020-03-31'),
            ('2020-04-01', '2020-06-30'),
            ('2020-07-01', '2020-09-30'),
            ('2020-10-01', '2020-12-31'),
            ('2021-01-01', '2021-03-31'),
            ('2021-04-01', '2021-06-30'),
            ('2021-07-01', '2021-09-30'),
            ('2021-10-01', '2021-12-31'),
        ]
        
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        portfolio_value = 100000.0
        
        print(f"Starting portfolio value: ${portfolio_value:,.2f}")
        
        for i, (start_date, end_date) in enumerate(quarters):
            # Get prices at start and end of quarter
            start_prices = {}
            end_prices = {}
            
            for symbol in symbols:
                start_data = self.dm.get_stock_prices(symbol, start_date, start_date)
                end_data = self.dm.get_stock_prices(symbol, end_date, end_date)
                
                if not start_data.empty and not end_data.empty:
                    start_prices[symbol] = start_data['close'].iloc[0]
                    end_prices[symbol] = end_data['close'].iloc[-1]
            
            if len(start_prices) == len(symbols):
                # Calculate equal weight portfolio return
                equal_weight_return = 0
                for symbol in symbols:
                    stock_return = float((end_prices[symbol] - start_prices[symbol]) / start_prices[symbol])
                    equal_weight_return += stock_return / len(symbols)
                
                portfolio_value = portfolio_value * (1 + float(equal_weight_return))
                
                print(f"Q{i+1} {start_date[:7]}: {equal_weight_return:8.2%} → ${portfolio_value:,.2f}")
        
        total_return = (portfolio_value - 100000.0) / 100000.0
        print(f"\nTotal return: {total_return:.2%}")
        
        # This should be positive for tech stocks in 2020-2021
        self.assertGreater(total_return, 0, 
                         "Quarterly rebalancing should be profitable for tech stocks")

def run_tech_stock_tests():
    """Run tech stock performance tests"""
    print("🧪 RUNNING TECH STOCK PERFORMANCE TESTS")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTechStockPerformance,
        TestPortfolioSimulation
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tech_stock_tests()
    sys.exit(0 if success else 1)
