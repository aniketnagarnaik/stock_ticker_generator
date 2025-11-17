#!/usr/bin/env python3
"""
Check which stocks we actually have data for in our backtesting
"""

import sys
sys.path.append('..')
from backtesting_experiments.postgres_data_manager import PostgresDataManager
from sqlalchemy import text

def check_available_stocks():
    """Check which stocks have data available"""
    dm = PostgresDataManager()
    
    print("🔍 CHECKING AVAILABLE STOCKS FOR BACKTESTING")
    print("=" * 60)
    
    # Get all symbols from our database
    session = dm._get_session()
    try:
        # Check stocks table
        result = session.execute(text("SELECT symbol, company_name FROM stocks ORDER BY symbol"))
        all_stocks = result.fetchall()
        
        print(f"📊 Total stocks in database: {len(all_stocks)}")
        print("\n📋 All available stocks:")
        for i, (symbol, company_name) in enumerate(all_stocks):
            print(f"  {i+1:3d}. {symbol:6s} - {company_name}")
        
        print("\n🔍 Checking which stocks have price data...")
        
        # Check which stocks have price data
        stocks_with_data = []
        for symbol, company_name in all_stocks:
            price_data = dm.get_stock_prices(symbol, '2020-01-01', '2025-12-31')
            if not price_data.empty:
                stocks_with_data.append((symbol, company_name, len(price_data)))
        
        print(f"\n📈 Stocks with price data: {len(stocks_with_data)}")
        print("\n📊 Stocks with price data (showing count):")
        for symbol, company_name, count in stocks_with_data:
            print(f"  {symbol:6s} - {company_name:30s} ({count:4d} records)")
        
        # Check which stocks have EPS data
        print("\n💰 Checking which stocks have EPS data...")
        stocks_with_eps = []
        for symbol, company_name in all_stocks:
            eps_data = dm.get_stock_eps(symbol, '2020-01-01', '2025-12-31')
            if not eps_data.empty:
                stocks_with_eps.append((symbol, company_name, len(eps_data)))
        
        print(f"\n📊 Stocks with EPS data: {len(stocks_with_eps)}")
        print("\n📈 Stocks with EPS data (showing count):")
        for symbol, company_name, count in stocks_with_eps:
            print(f"  {symbol:6s} - {company_name:30s} ({count:4d} records)")
        
        # Check which stocks have P/E data
        print("\n📊 Checking which stocks have P/E data...")
        stocks_with_pe = []
        for symbol, company_name in all_stocks:
            pe_data = dm.get_stock_pe_ratios(symbol, '2020-01-01', '2025-12-31')
            if not pe_data.empty:
                stocks_with_pe.append((symbol, company_name, len(pe_data)))
        
        print(f"\n📈 Stocks with P/E data: {len(stocks_with_pe)}")
        print("\n📊 Stocks with P/E data (showing count):")
        for symbol, company_name, count in stocks_with_pe:
            print(f"  {symbol:6s} - {company_name:30s} ({count:4d} records)")
        
        # Check which stocks have PEG data
        print("\n📈 Checking which stocks have PEG data...")
        stocks_with_peg = []
        for symbol, company_name in all_stocks:
            peg_data = dm.get_stock_peg_ratios(symbol, '2020-01-01', '2025-12-31')
            if not peg_data.empty:
                stocks_with_peg.append((symbol, company_name, len(peg_data)))
        
        print(f"\n📊 Stocks with PEG data: {len(stocks_with_peg)}")
        print("\n📈 Stocks with PEG data (showing count):")
        for symbol, company_name, count in stocks_with_peg:
            print(f"  {symbol:6s} - {company_name:30s} ({count:4d} records)")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY:")
        print(f"  Total stocks in database: {len(all_stocks)}")
        print(f"  Stocks with price data: {len(stocks_with_data)}")
        print(f"  Stocks with EPS data: {len(stocks_with_eps)}")
        print(f"  Stocks with P/E data: {len(stocks_with_pe)}")
        print(f"  Stocks with PEG data: {len(stocks_with_peg)}")
        
        # Find stocks with all data types
        symbols_with_price = {s[0] for s in stocks_with_data}
        symbols_with_eps = {s[0] for s in stocks_with_eps}
        symbols_with_pe = {s[0] for s in stocks_with_pe}
        symbols_with_peg = {s[0] for s in stocks_with_peg}
        
        complete_data_stocks = symbols_with_price & symbols_with_eps & symbols_with_pe & symbols_with_peg
        
        print(f"\n🎯 Stocks with ALL data types (price, EPS, P/E, PEG): {len(complete_data_stocks)}")
        if complete_data_stocks:
            print("📈 Complete data stocks:")
            for symbol in sorted(complete_data_stocks):
                company_name = next(name for s, name in all_stocks if s == symbol)
                print(f"  {symbol:6s} - {company_name}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_available_stocks()
