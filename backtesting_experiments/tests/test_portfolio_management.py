#!/usr/bin/env python3
"""
Unit Tests for Portfolio Management Logic
Test portfolio rebalancing, value calculation, and transaction handling
"""

import unittest
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append('..')
sys.path.append('.')

from quarterly_backtesting_engine import QuarterlyBacktestingEngine, PortfolioManager

class TestPortfolioManagerDetailed(unittest.TestCase):
    """Test PortfolioManager calculations in detail"""
    
    def setUp(self):
        self.portfolio = PortfolioManager(initial_capital=100000.0)
    
    def test_initial_state(self):
        """Test initial portfolio state"""
        self.assertEqual(self.portfolio.portfolio_value, 100000.0)
        self.assertEqual(self.portfolio.cash, 100000.0)
        self.assertEqual(len(self.portfolio.positions), 0)
        self.assertEqual(len(self.portfolio.transaction_history), 0)
    
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
        
        print(f"\n🧪 Testing initial buy with prices: {current_prices}")
        print(f"Initial cash: ${self.portfolio.cash:,.2f}")
        
        result = self.portfolio.rebalance_portfolio(target_stocks, current_prices)
        
        print(f"After rebalancing:")
        print(f"  Cash: ${self.portfolio.cash:,.2f}")
        print(f"  Positions: {self.portfolio.positions}")
        print(f"  Portfolio value: ${self.portfolio.portfolio_value:,.2f}")
        
        # Should have positions in both stocks
        self.assertIn('AAPL', self.portfolio.positions)
        self.assertIn('MSFT', self.portfolio.positions)
        
        # Should have equal dollar amounts in each stock (approximately)
        aapl_value = self.portfolio.positions['AAPL'] * 150.0
        msft_value = self.portfolio.positions['MSFT'] * 300.0
        
        print(f"  AAPL value: ${aapl_value:,.2f}")
        print(f"  MSFT value: ${msft_value:,.2f}")
        
        # Allow for small differences due to rounding and transaction costs
        self.assertAlmostEqual(aapl_value, msft_value, delta=1000.0)
        
        # Total portfolio value should be close to initial capital minus transaction costs
        total_value = self.portfolio.get_current_value(current_prices)
        print(f"  Total calculated value: ${total_value:,.2f}")
        
        # Should not lose more than 1% to transaction costs
        self.assertGreater(total_value, 99000.0)
    
    def test_rebalance_portfolio_sell_and_buy(self):
        """Test rebalancing when changing positions"""
        # Start with some positions
        self.portfolio.positions = {'AAPL': 100, 'MSFT': 50}
        self.portfolio.cash = 50000.0
        
        print(f"\n🧪 Testing sell and buy rebalancing")
        print(f"Initial positions: {self.portfolio.positions}")
        print(f"Initial cash: ${self.portfolio.cash:,.2f}")
        
        # Rebalance to different stocks
        target_stocks = ['GOOGL', 'TSLA']
        current_prices = {'GOOGL': 2500.0, 'TSLA': 200.0}
        
        result = self.portfolio.rebalance_portfolio(target_stocks, current_prices)
        
        print(f"After rebalancing:")
        print(f"  Cash: ${self.portfolio.cash:,.2f}")
        print(f"  Positions: {self.portfolio.positions}")
        
        # Should have new positions
        self.assertIn('GOOGL', self.portfolio.positions)
        self.assertIn('TSLA', self.portfolio.positions)
        
        # Should not have old positions
        self.assertNotIn('AAPL', self.portfolio.positions)
        self.assertNotIn('MSFT', self.portfolio.positions)
    
    def test_transaction_costs_calculation(self):
        """Test transaction costs are calculated correctly"""
        target_stocks = ['AAPL', 'MSFT']
        current_prices = {'AAPL': 150.0, 'MSFT': 300.0}
        
        result = self.portfolio.rebalance_portfolio(target_stocks, current_prices)
        
        print(f"\n🧪 Testing transaction costs")
        print(f"Transaction costs: ${result['transaction_costs']:,.2f}")
        
        # Transaction costs should be reasonable (0.1% of portfolio value)
        expected_costs = 100000.0 * 0.001  # 0.1%
        self.assertAlmostEqual(result['transaction_costs'], expected_costs, delta=100.0)
    
    def test_portfolio_value_consistency(self):
        """Test that portfolio value is consistent after rebalancing"""
        target_stocks = ['AAPL', 'MSFT']
        current_prices = {'AAPL': 150.0, 'MSFT': 300.0}
        
        initial_value = self.portfolio.get_current_value(current_prices)
        
        result = self.portfolio.rebalance_portfolio(target_stocks, current_prices)
        
        final_value = self.portfolio.get_current_value(current_prices)
        
        print(f"\n🧪 Testing portfolio value consistency")
        print(f"Initial value: ${initial_value:,.2f}")
        print(f"Final value: ${final_value:,.2f}")
        print(f"Difference: ${final_value - initial_value:,.2f}")
        
        # Portfolio value should decrease by transaction costs only
        expected_difference = -result['transaction_costs']
        self.assertAlmostEqual(final_value - initial_value, expected_difference, delta=10.0)

class TestQuarterlyBacktestingEngineDetailed(unittest.TestCase):
    """Test QuarterlyBacktestingEngine calculations in detail"""
    
    def setUp(self):
        self.dm = Mock()
        self.strategy_engine = Mock()
        self.backtest_engine = QuarterlyBacktestingEngine(
            start_date='2020-01-01',
            end_date='2020-12-31',
            initial_capital=100000.0
        )
        self.backtest_engine.dm = self.dm
        self.backtest_engine.strategy_engine = self.strategy_engine
    
    def test_get_stock_prices_on_date(self):
        """Test getting stock prices on a specific date"""
        # Mock price data
        price_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10, freq='D'),
            'close': [150.0 + i for i in range(10)]  # Increasing prices
        })
        
        self.dm.get_stock_prices.return_value = price_data
        
        prices = self.backtest_engine.get_stock_prices_on_date(['AAPL'], '2020-01-05')
        
        print(f"\n🧪 Testing stock price retrieval")
        print(f"Requested date: 2020-01-05")
        print(f"Retrieved price: ${prices['AAPL']:.2f}")
        
        self.assertIn('AAPL', prices)
        self.assertEqual(prices['AAPL'], 154.0)  # Should be close to target date
    
    def test_calculate_quarterly_return_simple(self):
        """Test quarterly return calculation with simple data"""
        # Set up portfolio with some positions
        self.backtest_engine.portfolio.positions = {'AAPL': 100}
        self.backtest_engine.portfolio.cash = 50000.0
        self.backtest_engine.portfolio.portfolio_value = 100000.0
        
        # Mock price data - stable prices
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
        
        print(f"\n🧪 Testing quarterly return calculation")
        print(f"Start value: ${start_value:,.2f}")
        print(f"Return: {return_pct:.2%}")
        
        # Should be close to 0 for stable prices
        self.assertAlmostEqual(return_pct, 0.0, delta=0.01)
    
    def test_calculate_quarterly_return_growth(self):
        """Test quarterly return calculation with growing prices"""
        # Set up portfolio with some positions
        self.backtest_engine.portfolio.positions = {'AAPL': 100}
        self.backtest_engine.portfolio.cash = 50000.0
        self.backtest_engine.portfolio.portfolio_value = 100000.0
        
        # Mock price data - growing prices
        price_data = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=10, freq='D'),
            'close': [150.0 + i * 5 for i in range(10)]  # Growing prices
        })
        
        self.dm.get_stock_prices.return_value = price_data
        
        # Calculate return over a quarter
        start_value = 100000.0
        return_pct = self.backtest_engine.calculate_quarterly_return(
            '2020-01-01', '2020-03-31', start_value
        )
        
        print(f"\n🧪 Testing quarterly return with growth")
        print(f"Start value: ${start_value:,.2f}")
        print(f"Return: {return_pct:.2%}")
        
        # Should be positive for growing prices
        self.assertGreater(return_pct, 0.0)

class TestRealWorldScenario(unittest.TestCase):
    """Test with real-world scenarios using actual data"""
    
    def setUp(self):
        from postgres_data_manager import PostgresDataManager
        self.dm = PostgresDataManager()
    
    def test_single_quarter_simulation(self):
        """Test a single quarter simulation with real data"""
        print("\n🧪 Testing single quarter simulation with real data")
        
        # Create backtesting engine
        engine = QuarterlyBacktestingEngine(
            start_date='2020-01-01',
            end_date='2020-03-31',
            initial_capital=100000.0
        )
        
        # Test Q1 2020
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        # Get prices at start of quarter
        start_prices = engine.get_stock_prices_on_date(symbols, '2020-01-01')
        
        print(f"Start prices: {start_prices}")
        
        if len(start_prices) >= 2:
            # Rebalance portfolio
            result = engine.portfolio.rebalance_portfolio(list(start_prices.keys()), start_prices)
            
            print(f"After rebalancing:")
            print(f"  Portfolio value: ${engine.portfolio.portfolio_value:,.2f}")
            print(f"  Cash: ${engine.portfolio.cash:,.2f}")
            print(f"  Positions: {engine.portfolio.positions}")
            
            # Get prices at end of quarter
            end_prices = engine.get_stock_prices_on_date(symbols, '2020-03-31')
            
            print(f"End prices: {end_prices}")
            
            # Calculate return
            start_value = engine.portfolio.portfolio_value
            end_value = engine.portfolio.get_current_value(end_prices)
            
            print(f"Start value: ${start_value:,.2f}")
            print(f"End value: ${end_value:,.2f}")
            print(f"Return: {(end_value - start_value) / start_value:.2%}")
            
            # The return should be reasonable (not -100%)
            self.assertGreater(end_value, start_value * 0.5)  # Should not lose more than 50%
    
    def test_momentum_selection_accuracy(self):
        """Test that momentum selection is working correctly"""
        print("\n🧪 Testing momentum selection accuracy")
        
        from momentum_strategy_engine import MomentumStrategyEngine
        
        strategy_engine = MomentumStrategyEngine(self.dm)
        
        # Test momentum scores for Q2 2020 start (when we know the performance)
        test_date = '2020-04-01'
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        
        print(f"Calculating momentum scores for {test_date}")
        
        scores = {}
        for symbol in symbols:
            try:
                combined_score = strategy_engine.calculate_combined_score(symbol, test_date)
                scores[symbol] = combined_score['combined_score']
                print(f"  {symbol}: {combined_score['combined_score']:.2f}")
            except Exception as e:
                print(f"  {symbol}: ERROR - {e}")
        
        # Sort by score
        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            print(f"\nSorted by momentum score:")
            for symbol, score in sorted_scores:
                print(f"  {symbol}: {score:.2f}")
            
            # TSLA should be near the top (it performed best in Q2 2020)
            top_symbols = [symbol for symbol, score in sorted_scores[:3]]
            print(f"\nTop 3 symbols: {top_symbols}")
            
            # TSLA should be in top 3
            self.assertIn('TSLA', top_symbols)

class TestPortfolioValueTracking(unittest.TestCase):
    """Test portfolio value tracking throughout the backtesting process"""
    
    def test_portfolio_value_never_goes_to_zero(self):
        """Test that portfolio value never goes to zero unexpectedly"""
        print("\n🧪 Testing portfolio value never goes to zero")
        
        from postgres_data_manager import PostgresDataManager
        from momentum_strategy_engine import MomentumStrategyEngine
        
        dm = PostgresDataManager()
        strategy_engine = MomentumStrategyEngine(dm)
        
        # Create backtesting engine
        engine = QuarterlyBacktestingEngine(
            start_date='2020-01-01',
            end_date='2020-06-30',  # Just 2 quarters
            initial_capital=100000.0
        )
        
        # Track portfolio value through quarters
        portfolio_values = []
        
        # Simulate Q1
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        q1_prices = engine.get_stock_prices_on_date(symbols, '2020-01-01')
        
        if len(q1_prices) >= 2:
            result = engine.portfolio.rebalance_portfolio(list(q1_prices.keys()), q1_prices)
            portfolio_values.append(engine.portfolio.portfolio_value)
            
            print(f"Q1 Portfolio value: ${engine.portfolio.portfolio_value:,.2f}")
            
            # Simulate Q2
            q2_prices = engine.get_stock_prices_on_date(symbols, '2020-04-01')
            result = engine.portfolio.rebalance_portfolio(list(q2_prices.keys()), q2_prices)
            portfolio_values.append(engine.portfolio.portfolio_value)
            
            print(f"Q2 Portfolio value: ${engine.portfolio.portfolio_value:,.2f}")
            
            # Portfolio value should never be zero or negative
            for i, value in enumerate(portfolio_values):
                self.assertGreater(value, 0, f"Portfolio value went to zero in quarter {i+1}")
                print(f"  Quarter {i+1}: ${value:,.2f}")

def run_portfolio_tests():
    """Run all portfolio management tests"""
    print("🧪 RUNNING PORTFOLIO MANAGEMENT TESTS")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPortfolioManagerDetailed,
        TestQuarterlyBacktestingEngineDetailed,
        TestRealWorldScenario,
        TestPortfolioValueTracking
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PORTFOLIO TEST SUMMARY:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  {test}")
    
    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  {test}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_portfolio_tests()
    sys.exit(0 if success else 1)

