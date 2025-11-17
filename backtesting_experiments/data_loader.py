#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Loader for Momentum Trading System
Loads historical data from DefeatBeta into PostgreSQL for 5 test stocks
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

sys.path.append('..')
from data_providers.defeatbeta_provider import DefeatBetaProvider
from postgres_data_manager import PostgresDataManager

class DataLoader:
    """Loads historical data from DefeatBeta to PostgreSQL"""
    
    def __init__(self):
        self.defeatbeta = DefeatBetaProvider()
        self.dm = PostgresDataManager()
        print("📊 DataLoader initialized")
    
    def load_stock_data(self, symbol: str, years_back: int = None) -> bool:
        """Load all available data for a single stock"""
        print(f"📈 Loading data for {symbol}...")
        
        try:
            # Get stock info from DefeatBeta
            stock_info = self.defeatbeta.get_stock_info(symbol)
            
            if not stock_info:
                print(f"❌ No data found for {symbol}")
                return False
            
            # Use all available data unless years_back is specified
            if years_back is not None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=years_back * 365)
                print(f"  📅 Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            else:
                print(f"  📅 Loading all available data for {symbol}")
            
            # Load price data
            if 'price_data' in stock_info and stock_info['price_data'] is not None:
                price_data = stock_info['price_data']
                
                # Rename report_date to date for consistency
                if 'report_date' in price_data.columns:
                    price_data = price_data.rename(columns={'report_date': 'date'})
                elif 'date' not in price_data.columns:
                    print(f"  ⚠️ No date column found in price data for {symbol}")
                    return False
                
                price_data['date'] = pd.to_datetime(price_data['date'])
                
                # Filter by date range if specified
                if years_back is not None:
                    price_data = price_data[price_data['date'] >= start_date]
                
                if not price_data.empty:
                    success = self.dm.load_stock_prices(symbol, price_data)
                    if not success:
                        return False
                    print(f"  ✅ Loaded {len(price_data)} price records")
                else:
                    print(f"  ⚠️ No price data in date range for {symbol}")
            
            # Load EPS data
            if 'eps_history' in stock_info and stock_info['eps_history'] is not None:
                eps_data = stock_info['eps_history']
                if isinstance(eps_data, dict) and 'data' in eps_data:
                    # Convert nested data to DataFrame
                    eps_list = eps_data['data']
                    eps_df = pd.DataFrame(eps_list)
                    eps_df['date'] = pd.to_datetime(eps_df['date'])
                    
                    # Filter by date range if specified
                    if years_back is not None:
                        eps_df = eps_df[eps_df['date'] >= start_date]
                    
                    # Clean EPS data
                    eps_df = eps_df.dropna(subset=['eps'])
                    eps_df = eps_df[eps_df['eps'].notna()]
                    eps_df = eps_df[eps_df['eps'] != 'NaT']
                    eps_df = eps_df[eps_df['eps'].apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x))]
                    
                    if not eps_df.empty:
                        success = self.dm.load_stock_eps(symbol, eps_df)
                        if not success:
                            return False
                        print(f"  ✅ Loaded {len(eps_df)} EPS records")
                    else:
                        print(f"  ⚠️ No EPS data in date range for {symbol}")
                else:
                    print(f"  ⚠️ EPS data format not recognized for {symbol}")
            
            # Load P/E ratio data
            try:
                pe_data = self.defeatbeta.get_pe_ratios(symbol)
                if pe_data is not None and not pe_data.empty:
                    # Rename report_date to date for consistency
                    if 'report_date' in pe_data.columns:
                        pe_data = pe_data.rename(columns={'report_date': 'date'})
                    elif 'date' not in pe_data.columns:
                        print(f"  ⚠️ No date column found in P/E data for {symbol}")
                        pe_data = None
                    
                    if pe_data is not None:
                        pe_data['date'] = pd.to_datetime(pe_data['date'])
                        
                        # Filter by date range if specified
                        if years_back is not None:
                            pe_data = pe_data[pe_data['date'] >= start_date]
                        
                        # Clean infinite values and invalid data
                        pe_data = pe_data.replace([float('inf'), float('-inf')], None)
                        pe_data = pe_data.dropna(subset=['pe'])
                        pe_data = pe_data[pe_data['pe'].notna()]
                        pe_data = pe_data[pe_data['pe'] != 'NaT']
                        
                        # Remove any remaining invalid values
                        pe_data = pe_data[pe_data['pe'].apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x))]
                        
                        if not pe_data.empty:
                            success = self.dm.load_stock_pe_ratios(symbol, pe_data)
                            if not success:
                                return False
                            print(f"  ✅ Loaded {len(pe_data)} P/E records")
                        else:
                            print(f"  ⚠️ No P/E data in date range for {symbol}")
                else:
                    print(f"  ⚠️ No P/E data available for {symbol}")
            except Exception as e:
                print(f"  ⚠️ Error loading P/E data for {symbol}: {e}")
            
            # Load PEG ratio data
            try:
                peg_data = self.defeatbeta.get_peg_ratios(symbol)
                if peg_data is not None and not peg_data.empty:
                    # Rename report_date to date for consistency
                    if 'report_date' in peg_data.columns:
                        peg_data = peg_data.rename(columns={'report_date': 'date'})
                    elif 'date' not in peg_data.columns:
                        print(f"  ⚠️ No date column found in PEG data for {symbol}")
                        peg_data = None
                    
                    if peg_data is not None:
                        peg_data['date'] = pd.to_datetime(peg_data['date'])
                        
                        # Filter by date range if specified
                        if years_back is not None:
                            peg_data = peg_data[peg_data['date'] >= start_date]
                        
                        # Clean infinite values and NaT
                        peg_data = peg_data.replace([float('inf'), float('-inf')], None)
                        peg_data = peg_data.dropna(subset=['peg'])
                        
                        # Clean any remaining invalid values
                        peg_data = peg_data[peg_data['peg'].notna()]
                        peg_data = peg_data[peg_data['peg'] != 'NaT']
                        
                        if not peg_data.empty:
                            success = self.dm.load_stock_peg_ratios(symbol, peg_data)
                            if not success:
                                return False
                            print(f"  ✅ Loaded {len(peg_data)} PEG records")
                        else:
                            print(f"  ⚠️ No PEG data in date range for {symbol}")
                else:
                    print(f"  ⚠️ No PEG data available for {symbol}")
            except Exception as e:
                print(f"  ⚠️ Error loading PEG data for {symbol}: {e}")
            
            print(f"✅ Successfully loaded data for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading data for {symbol}: {e}")
            return False
    
    def load_spy_data(self, years_back: int = None) -> bool:
        """Load SPY benchmark data from CSV file"""
        print("📊 Loading SPY benchmark data from CSV file...")
        
        try:
            spy_csv_path = "/Users/aniketnagarnaik/Downloads/archive/spy-historical.csv"
            
            if not os.path.exists(spy_csv_path):
                print(f"❌ SPY CSV file not found at: {spy_csv_path}")
                return False
            
            # Read SPY CSV file
            spy_data = pd.read_csv(spy_csv_path)
            print(f"📊 Loaded SPY CSV with {len(spy_data)} records")
            
            # Check column names and standardize
            print(f"📋 SPY CSV columns: {list(spy_data.columns)}")
            
            # Standardize column names (common variations)
            column_mapping = {
                'Date': 'date',
                'date': 'date',
                'DATE': 'date',
                'Open': 'open',
                'open': 'open',
                'OPEN': 'open',
                'High': 'high',
                'high': 'high',
                'HIGH': 'high',
                'Low': 'low',
                'low': 'low',
                'LOW': 'low',
                'Close': 'close',
                'close': 'close',
                'CLOSE': 'close',
                'Volume': 'volume',
                'volume': 'volume',
                'VOLUME': 'volume',
                'Adj Close': 'adj_close',  # Keep adjusted close separate
                'adj_close': 'adj_close'
            }
            
            # Rename columns
            spy_data = spy_data.rename(columns=column_mapping)
            
            # Convert date column
            spy_data['date'] = pd.to_datetime(spy_data['date'])
            
            # Remove duplicates and sort by date
            spy_data = spy_data.drop_duplicates(subset=['date']).sort_values('date')
            
            # Use all available data unless years_back is specified
            if years_back is not None:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=years_back * 365)
                
                # Filter data by date range
                spy_data = spy_data[spy_data['date'] >= start_date]
                print(f"📅 Filtered to last {years_back} years: {len(spy_data)} records")
            else:
                print(f"📅 Using all available data: {len(spy_data)} records")
            
            if spy_data.empty:
                print("⚠️ No SPY data in date range")
                return False
            
            # Ensure we have required columns
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in spy_data.columns]
            
            if missing_columns:
                print(f"⚠️ Missing columns in SPY data: {missing_columns}")
                # Try to use available columns
                if 'close' in spy_data.columns:
                    # Use close price for all OHLC if missing
                    for col in ['open', 'high', 'low']:
                        if col not in spy_data.columns:
                            spy_data[col] = spy_data['close']
                    if 'volume' not in spy_data.columns:
                        spy_data['volume'] = 1000000  # Default volume
                else:
                    print("❌ No close price data available")
                    return False
            
            # Clean data - ensure all numeric columns are properly formatted
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in spy_data.columns:
                    # Convert to numeric, handling any string values
                    spy_data[col] = pd.to_numeric(spy_data[col], errors='coerce')
                    # Remove rows with NaN values
                    spy_data = spy_data.dropna(subset=[col])
            
            # Reset index after cleaning
            spy_data = spy_data.reset_index(drop=True)
            
            print(f"📊 Cleaned SPY data: {len(spy_data)} records from {spy_data['date'].min()} to {spy_data['date'].max()}")
            
            # Load to PostgreSQL
            success = self.dm.load_spy_data(spy_data)
            if success:
                print(f"✅ Loaded {len(spy_data)} SPY records from CSV")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Error loading SPY data from CSV: {e}")
            return False
    
    def load_test_stocks(self, symbols: List[str], years_back: int = None) -> Dict[str, bool]:
        """Load data for multiple test stocks"""
        print(f"🚀 Loading data for {len(symbols)} test stocks...")
        
        results = {}
        
        # Load SPY data first - use all available data for backtesting
        spy_success = self.load_spy_data(years_back=None)  # Load all SPY data
        if not spy_success:
            print("❌ Failed to load SPY data - aborting")
            return results
        
        # Load individual stock data - use all available data
        for symbol in symbols:
            success = self.load_stock_data(symbol, years_back=None)  # Load all available data
            results[symbol] = success
        
        # Summary
        successful = sum(1 for success in results.values() if success)
        print(f"\n📊 Loading Summary:")
        print(f"  ✅ Successful: {successful}/{len(symbols)} stocks")
        print(f"  ❌ Failed: {len(symbols) - successful}/{len(symbols)} stocks")
        
        for symbol, success in results.items():
            status = "✅" if success else "❌"
            print(f"    {status} {symbol}")
        
        return results
    
    def verify_data_loaded(self, symbols: List[str]) -> Dict[str, Dict]:
        """Verify that data was loaded correctly"""
        print("🔍 Verifying loaded data...")
        
        verification = {}
        
        for symbol in symbols:
            print(f"  📊 Checking {symbol}...")
            
            # Get date range
            start_date, end_date = self.dm.get_data_date_range(symbol)
            
            # Count records
            price_data = self.dm.get_stock_prices(symbol, start_date or '2020-01-01', end_date or '2024-12-31')
            eps_data = self.dm.get_stock_eps(symbol, start_date or '2020-01-01', end_date or '2024-12-31')
            pe_data = self.dm.get_stock_pe_ratios(symbol, start_date or '2020-01-01', end_date or '2024-12-31')
            peg_data = self.dm.get_stock_peg_ratios(symbol, start_date or '2020-01-01', end_date or '2024-12-31')
            
            verification[symbol] = {
                'date_range': f"{start_date} to {end_date}" if start_date and end_date else "No data",
                'price_records': len(price_data),
                'eps_records': len(eps_data),
                'pe_records': len(pe_data),
                'peg_records': len(peg_data)
            }
            
            print(f"    📅 Date range: {verification[symbol]['date_range']}")
            print(f"    📈 Price records: {verification[symbol]['price_records']}")
            print(f"    💰 EPS records: {verification[symbol]['eps_records']}")
            print(f"    📊 P/E records: {verification[symbol]['pe_records']}")
            print(f"    📈 PEG records: {verification[symbol]['peg_records']}")
        
        return verification

if __name__ == "__main__":
    print("🚀 Data Loader - Loading Test Stocks")
    print("=" * 60)
    
    # Test with 5 major stocks
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    loader = DataLoader()
    
    # Clear existing data
    print("🗑️ Clearing existing data...")
    loader.dm.clear_data()
    
    # Load data - use all available data for comprehensive backtesting
    results = loader.load_test_stocks(test_symbols, years_back=None)
    
    # Verify data
    print("\n" + "=" * 60)
    verification = loader.verify_data_loaded(test_symbols)
    
    print("\n" + "=" * 60)
    print("✅ Data loading complete!")
    
    # Show summary
    print("\n📊 Final Summary:")
    for symbol, data in verification.items():
        print(f"  {symbol}: {data['price_records']} prices, {data['eps_records']} EPS, "
              f"{data['pe_records']} P/E, {data['peg_records']} PEG")
