#!/usr/bin/env python3
"""
Unit Tests for Backtesting Engine
Test individual components to verify calculations are correct
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append('..')
sys.path.append('.')

from postgres_data_manager import PostgresDataManager
from momentum_strategy_engine import MomentumStrategyEngine
from quarterly_backtesting_engine import QuarterlyBacktestingEngine, PortfolioManager

class TestPortfolioManager(unittest.TestCase):
    """Test PortfolioManager calculations"""
    
    def setUp(self):
        self.portfolio = PortfolioManager(initial_capital=100000.0)
    
    def test_initial_portfolio_value(self):
        """Test initial portfolio value"""
        self.assertEqual(self.portfolio.portfolio_value, 100000.0)
        self.assertEqual(self.portfolio.cash, 100000.0)
        self.assertEqual(len(self.portfolio.positions), 0)
    
    def test_get_current_value_no_positions(self):
        """Test get_current_value with no positions"""
        current_prices = {'AAPL': 150.0, 'MSFT': 300.0}
        value = self.portfolio.get_current_value(current_prices)
        self.assertEqual(value, 100000.0)  # Should equal cash
    
    def test_get_current_value_with_positions(self):
        """Test get_current_value with positions"""
        # Add some positions
        self.portfolio.positions = {'AAPL': 100, 'MSFT': 50}
        self.portfolio.cash = 50000.0
        
        current_prices = {'AAPL': 150.0, 'MSFT': 300.0}
        value = self.portfolio.get_current_value(current_prices)
        
        expected_value = 50000.0 + (100 * 150.0) + (50 * 300.0)
        self.assertEqual(value, expected_value)
    
    def test_rebalance_portfolio_buy_only(self):
        """Test rebalancing when buying stocks for first time"""
        target_stocks = ['AAPL', 'MSFT']
        current_prices = {'AAPL': 150.0, 'MSFT': 300.0}
        
        result = self.portfolio.rebalance_portfolio(target_stocks, current_prices)
        
        # Should have positions in both stocks
        self.assertIn('AAPL', self.portfolio.positions)
        self.assertIn('MSFT', self.portfolio.positions)
        
        # Should have equal dollar amounts in each stock
        aapl_value = self.portfolio.positions['AAPL'] * 150.0
        msft_value = self.portfolio.positions['MSFT'] * 300.0
        
        # Allow for small differences due to rounding
        self.assertAlmostEqual(aapl_value, msft_value, delta=1.0)
        
        # Total portfolio value should be close to initial capital minus transaction costs
        total_value = self.portfolio.get_current_value(current_prices)
        self.assertAlmostEqual(total_value, 100000.0, delta=1000.0)
    
    def test_rebalance_portfolio_sell_and_buy(self):
        """Test rebalancing when changing positions"""
        # Start with some positions
        self.portfolio.positions = {'AAPL': 100, 'MSFT': 50}
        self.portfolio.cash = 50000.0
        
        # Rebalance to different stocks
        target_stocks = ['GOOGL', 'TSLA']
        current_prices = {'GOOGL': 2500.0, 'TSLA': 200.0}
        
        result = self.portfolio.rebalance_portfolio(target_stocks, current_prices)
        
        # Should have new positions
        self.assertIn('GOOGL', self.portfolio.positions)
        self.assertIn('TSLA', self.portfolio.positions)
        
        # Should not have old positions
        self.assertNotIn('AAPL', self.portfolio.positions)
        self.assertNotIn('MSFT', self.portfolio.positions)

class TestMomentumStrategyEngine(unittest.TestCase):
    """Test MomentumStrategyEngine calculations"""
    
    def setUp(self):
        self.dm = Mock(spec=PostgresDataManager)
        self.engine = MomentumStrategyEngine(self.dm)
    
    def test_calculate_rs_vs_spy_simple(self):
        """Test RS vs SPY calculation with simple data"""
        # Mock data
        stock_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'close': [100 + i * 0.1 for i in range(100)]  # Upward trend
        })
        
        spy_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'close': [200 + i * 0.05 for i in range(100)]  # Slower upward trend
        })
        
        self.dm.get_stock_prices.return_value = stock_data
        self.dm.get_spy_data.return_value = spy_data
        
        rs_score = self.engine.calculate_rs_vs_spy('AAPL', '2020-04-10')
        
        # Stock should outperform SPY (positive RS)
        self.assertGreater(rs_score, 0)
    
    def test_calculate_eps_momentum_simple(self):
        """Test EPS momentum calculation"""
        # Mock EPS data
        eps_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10, freq='Q'),
            'eps': [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9]  # Growing EPS
        })
        
        self.dm.get_stock_eps.return_value = eps_data
        
        eps_momentum = self.engine.calculate_eps_momentum('AAPL', '2020-10-01')
        
        # Should be positive for growing EPS
        self.assertGreater(eps_momentum, 0)
    
    def test_calculate_price_momentum_simple(self):
        """Test price momentum calculation"""
        # Mock price data
        price_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=100, freq='D'),
            'close': [100 + i * 0.5 for i in range(100)]  # Strong upward trend
        })
        
        self.dm.get_stock_prices.return_value = price_data
        
        price_momentum = self.engine.calculate_price_momentum('AAPL', '2020-04-10')
        
        # Should be positive for upward trend
        self.assertGreater(price_momentum, 0)

class TestQuarterlyBacktestingEngine(unittest.TestCase):
    """Test QuarterlyBacktestingEngine calculations"""
    
    def setUp(self):
        self.dm = Mock(spec=PostgresDataManager)
        self.strategy_engine = Mock(spec=MomentumStrategyEngine)
        self.backtest_engine = QuarterlyBacktestingEngine(
            start_date='2020-01-01',
            end_date='2020-12-31',
            initial_capital=100000.0
        )
        self.backtest_engine.dm = self.dm
        self.backtest_engine.strategy_engine = self.strategy_engine
    
    def test_calculate_quarterly_return_simple(self):
        """Test quarterly return calculation"""
        # Set up portfolio with some positions
        self.backtest_engine.portfolio.positions = {'AAPL': 100}
        self.backtest_engine.portfolio.cash = 50000.0
        self.backtest_engine.portfolio.portfolio_value = 100000.0
        
        # Mock price data
        price_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10, freq='D'),
            'close': [150.0] * 10  # Stable price
        })
        
        self.dm.get_stock_prices.return_value = price_data
        
        # Calculate return over a quarter
        start_value = 100000.0
        return_pct = self.backtest_engine.calculate_quarterly_return(
            '2020-01-01', '2020-03-31', start_value
        )
        
        # Should be close to 0 for stable prices
        self.assertAlmostEqual(return_pct, 0.0, delta=0.01)
    
    def test_get_stock_prices_on_date(self):
        """Test getting stock prices on a specific date"""
        # Mock price data
        price_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10, freq='D'),
            'close': [150.0 + i for i in range(10)]  # Increasing prices
        })
        
        self.dm.get_stock_prices.return_value = price_data
        
        prices = self.backtest_engine.get_stock_prices_on_date(['AAPL'], '2020-01-05')
        
        self.assertIn('AAPL', prices)
        self.assertEqual(prices['AAPL'], 154.0)  # Should be close to target date

class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and consistency"""
    
    def test_stock_price_data_consistency(self):
        """Test that stock price data is consistent"""
        dm = PostgresDataManager()
        
        # Test a few stocks
        test_stocks = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in test_stocks:
            with self.subTest(symbol=symbol):
                # Get price data
                price_data = dm.get_stock_prices(symbol, '2020-01-01', '2020-12-31')
                
                if not price_data.empty:
                    # Check data integrity
                    self.assertFalse(price_data['close'].isna().any(), 
                                   f"{symbol} has NaN close prices")
                    self.assertTrue((price_data['close'] > 0).all(), 
                                  f"{symbol} has non-positive close prices")
                    
                    # Check date ordering
                    self.assertTrue(price_data['date'].is_monotonic_increasing, 
                                  f"{symbol} dates are not in order")
    
    def test_eps_data_consistency(self):
        """Test that EPS data is consistent"""
        dm = PostgresDataManager()
        
        test_stocks = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in test_stocks:
            with self.subTest(symbol=symbol):
                eps_data = dm.get_stock_eps(symbol, '2020-01-01', '2020-12-31')
                
                if not eps_data.empty:
                    # Check data integrity
                    self.assertFalse(eps_data['eps'].isna().any(), 
                                   f"{symbol} has NaN EPS values")
                    
                    # Check date ordering
                    self.assertTrue(eps_data['date'].is_monotonic_increasing, 
                                  f"{symbol} EPS dates are not in order")

class TestRealWorldScenario(unittest.TestCase):
    """Test with real-world scenarios"""
    
    def test_tech_stocks_2020_performance(self):
        """Test that tech stocks performed well in 2020"""
        dm = PostgresDataManager()
        
        # Get 2020 data for major tech stocks
        tech_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        for symbol in tech_stocks:
            with self.subTest(symbol=symbol):
                # Get price data for 2020
                price_data = dm.get_stock_prices(symbol, '2020-01-01', '2020-12-31')
                
                if not price_data.empty and len(price_data) > 1:
                    start_price = price_data['close'].iloc[0]
                    end_price = price_data['close'].iloc[-1]
                    
                    annual_return = (end_price - start_price) / start_price
                    
                    # Tech stocks should have performed well in 2020
                    print(f"{symbol}: {annual_return:.2%} return in 2020")
                    
                    # Most tech stocks had positive returns in 2020
                    if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
                        self.assertGreater(annual_return, 0, 
                                         f"{symbol} should have positive return in 2020")
    
    def test_portfolio_value_calculation_real_data(self):
        """Test portfolio value calculation with real data"""
        dm = PostgresDataManager()
        
        # Create a simple portfolio
        portfolio = PortfolioManager(100000.0)
        
        # Get real prices for a specific date
        test_date = '2020-06-30'
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        prices = {}
        for symbol in symbols:
            price_data = dm.get_stock_prices(symbol, test_date, test_date)
            if not price_data.empty:
                prices[symbol] = price_data['close'].iloc[0]
        
        if len(prices) >= 2:
            # Rebalance portfolio
            result = portfolio.rebalance_portfolio(list(prices.keys()), prices)
            
            # Calculate portfolio value
            portfolio_value = portfolio.get_current_value(prices)
            
            # Portfolio value should be reasonable
            self.assertGreater(portfolio_value, 50000.0)  # Should not lose more than 50%
            self.assertLess(portfolio_value, 200000.0)     # Should not gain more than 100%
            
            print(f"Portfolio value on {test_date}: ${portfolio_value:,.2f}")
            print(f"Positions: {portfolio.positions}")
            print(f"Cash: ${portfolio.cash:,.2f}")

def run_all_tests():
    """Run all unit tests"""
    print("🧪 RUNNING UNIT TESTS FOR BACKTESTING ENGINE")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPortfolioManager,
        TestMomentumStrategyEngine,
        TestQuarterlyBacktestingEngine,
        TestDataIntegrity,
        TestRealWorldScenario
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
    success = run_all_tests()
    sys.exit(0 if success else 1)

