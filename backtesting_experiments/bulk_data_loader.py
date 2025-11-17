#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bulk Data Loader for Momentum Trading System
Automatically loads data for all stocks from the stocks table
"""

import os
import sys
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

sys.path.append('..')
from data_providers.defeatbeta_provider import DefeatBetaProvider
from postgres_data_manager import PostgresDataManager
from sqlalchemy import text

class BulkDataLoader:
    """Automated bulk data loader for all stocks in the database"""
    
    def __init__(self, batch_size: int = 10, delay_between_batches: float = 2.0):
        self.defeatbeta = DefeatBetaProvider()
        self.dm = PostgresDataManager()
        self.batch_size = batch_size
        self.delay_between_batches = delay_between_batches
        print("🚀 BulkDataLoader initialized")
        print(f"📊 Batch size: {batch_size}, Delay: {delay_between_batches}s")
    
    def get_all_stock_symbols(self) -> List[str]:
        """Get all stock symbols from the stocks table"""
        print("📋 Fetching all stock symbols from database...")
        
        session = self.dm._get_session()
        try:
            result = session.execute(text('SELECT symbol FROM stocks ORDER BY symbol'))
            symbols = [row[0] for row in result.fetchall()]
            print(f"✅ Found {len(symbols)} stocks in database")
            return symbols
        finally:
            session.close()
    
    def get_stocks_with_data(self) -> List[str]:
        """Get list of stocks that already have data loaded"""
        print("🔍 Checking which stocks already have data...")
        
        session = self.dm._get_session()
        try:
            result = session.execute(text('''
                SELECT DISTINCT symbol 
                FROM stock_prices 
                ORDER BY symbol
            '''))
            symbols_with_data = [row[0] for row in result.fetchall()]
            print(f"📊 {len(symbols_with_data)} stocks already have data")
            return symbols_with_data
        finally:
            session.close()
    
    def load_stock_data_batch(self, symbols: List[str], years_back: int = None) -> Dict[str, bool]:
        """Load data for a batch of stocks"""
        print(f"📦 Processing batch of {len(symbols)} stocks: {symbols}")
        
        results = {}
        
        for symbol in symbols:
            try:
                print(f"  📈 Loading {symbol}...")
                
                # Get stock info from DefeatBeta
                stock_info = self.defeatbeta.get_stock_info(symbol)
                
                if not stock_info:
                    print(f"    ❌ No data found for {symbol}")
                    results[symbol] = False
                    continue
                
                # Load price data
                if 'price_data' in stock_info and stock_info['price_data'] is not None:
                    price_data = stock_info['price_data']
                    
                    # Rename report_date to date for consistency
                    if 'report_date' in price_data.columns:
                        price_data = price_data.rename(columns={'report_date': 'date'})
                    elif 'date' not in price_data.columns:
                        print(f"    ⚠️ No date column found in price data for {symbol}")
                        results[symbol] = False
                        continue
                    
                    price_data['date'] = pd.to_datetime(price_data['date'])
                    
                    # Filter by date range if specified
                    if years_back is not None:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=years_back * 365)
                        price_data = price_data[price_data['date'] >= start_date]
                    
                    if not price_data.empty:
                        success = self.dm.load_stock_prices(symbol, price_data)
                        if success:
                            print(f"    ✅ Loaded {len(price_data)} price records")
                        else:
                            print(f"    ❌ Failed to load price data for {symbol}")
                            results[symbol] = False
                            continue
                    else:
                        print(f"    ⚠️ No price data for {symbol}")
                        results[symbol] = False
                        continue
                else:
                    print(f"    ⚠️ No price data available for {symbol}")
                    results[symbol] = False
                    continue
                
                # Load EPS data
                if 'eps_history' in stock_info and stock_info['eps_history'] is not None:
                    eps_data = stock_info['eps_history']
                    if isinstance(eps_data, dict) and 'data' in eps_data:
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
                            if success:
                                print(f"    ✅ Loaded {len(eps_df)} EPS records")
                
                # Load P/E ratio data
                try:
                    pe_data = self.defeatbeta.get_pe_ratios(symbol)
                    if pe_data is not None and not pe_data.empty:
                        if 'report_date' in pe_data.columns:
                            pe_data = pe_data.rename(columns={'report_date': 'date'})
                        elif 'date' not in pe_data.columns:
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
                            pe_data = pe_data[pe_data['pe'].apply(lambda x: isinstance(x, (int, float)) and not pd.isna(x))]
                            
                            if not pe_data.empty:
                                success = self.dm.load_stock_pe_ratios(symbol, pe_data)
                                if success:
                                    print(f"    ✅ Loaded {len(pe_data)} P/E records")
                except Exception as e:
                    print(f"    ⚠️ Error loading P/E data for {symbol}: {e}")
                
                # Load PEG ratio data
                try:
                    peg_data = self.defeatbeta.get_peg_ratios(symbol)
                    if peg_data is not None and not peg_data.empty:
                        if 'report_date' in peg_data.columns:
                            peg_data = peg_data.rename(columns={'report_date': 'date'})
                        elif 'date' not in peg_data.columns:
                            peg_data = None
                        
                        if peg_data is not None:
                            peg_data['date'] = pd.to_datetime(peg_data['date'])
                            
                            # Filter by date range if specified
                            if years_back is not None:
                                peg_data = peg_data[peg_data['date'] >= start_date]
                            
                            # Clean infinite values and NaT
                            peg_data = peg_data.replace([float('inf'), float('-inf')], None)
                            peg_data = peg_data.dropna(subset=['peg'])
                            peg_data = peg_data[peg_data['peg'].notna()]
                            peg_data = peg_data[peg_data['peg'] != 'NaT']
                            
                            if not peg_data.empty:
                                success = self.dm.load_stock_peg_ratios(symbol, peg_data)
                                if success:
                                    print(f"    ✅ Loaded {len(peg_data)} PEG records")
                except Exception as e:
                    print(f"    ⚠️ Error loading PEG data for {symbol}: {e}")
                
                results[symbol] = True
                print(f"    ✅ Successfully loaded data for {symbol}")
                
            except Exception as e:
                print(f"    ❌ Error loading data for {symbol}: {e}")
                results[symbol] = False
        
        return results
    
    def load_all_stocks_data(self, years_back: int = None, skip_existing: bool = True) -> Dict[str, bool]:
        """Load data for all stocks in the database"""
        print("🚀 Starting bulk data loading for all stocks...")
        print("=" * 80)
        
        # Get all stock symbols
        all_symbols = self.get_all_stock_symbols()
        
        # Get stocks that already have data (if skip_existing is True)
        if skip_existing:
            existing_symbols = self.get_stocks_with_data()
            symbols_to_load = [s for s in all_symbols if s not in existing_symbols]
            print(f"📊 Skipping {len(existing_symbols)} stocks that already have data")
            print(f"📈 Will load data for {len(symbols_to_load)} stocks")
        else:
            symbols_to_load = all_symbols
            print(f"📈 Will load data for all {len(symbols_to_load)} stocks")
        
        if not symbols_to_load:
            print("✅ All stocks already have data loaded!")
            return {}
        
        # Process in batches
        all_results = {}
        total_batches = (len(symbols_to_load) + self.batch_size - 1) // self.batch_size
        
        print(f"📦 Processing {len(symbols_to_load)} stocks in {total_batches} batches")
        print()
        
        for batch_num in range(total_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(symbols_to_load))
            batch_symbols = symbols_to_load[start_idx:end_idx]
            
            print(f"🔄 Batch {batch_num + 1}/{total_batches} ({len(batch_symbols)} stocks)")
            print("-" * 60)
            
            # Load data for this batch
            batch_results = self.load_stock_data_batch(batch_symbols, years_back)
            all_results.update(batch_results)
            
            # Progress update
            successful = sum(1 for success in batch_results.values() if success)
            print(f"📊 Batch {batch_num + 1} Results: {successful}/{len(batch_symbols)} successful")
            
            # Delay between batches (except for the last batch)
            if batch_num < total_batches - 1:
                print(f"⏳ Waiting {self.delay_between_batches}s before next batch...")
                time.sleep(self.delay_between_batches)
            
            print()
        
        # Final summary
        total_successful = sum(1 for success in all_results.values() if success)
        total_failed = len(all_results) - total_successful
        
        print("=" * 80)
        print("📊 BULK LOADING SUMMARY")
        print("=" * 80)
        print(f"✅ Successful: {total_successful}/{len(all_results)} stocks")
        print(f"❌ Failed: {total_failed}/{len(all_results)} stocks")
        print(f"📈 Success Rate: {total_successful/len(all_results)*100:.1f}%")
        
        if total_failed > 0:
            print("\n❌ Failed stocks:")
            for symbol, success in all_results.items():
                if not success:
                    print(f"  - {symbol}")
        
        return all_results
    
    def verify_data_loading(self) -> Dict[str, Dict]:
        """Verify data loading results"""
        print("🔍 Verifying data loading results...")
        print("=" * 60)
        
        # Get all symbols with data
        symbols_with_data = self.get_stocks_with_data()
        
        verification = {}
        for symbol in symbols_with_data[:10]:  # Check first 10 for verification
            print(f"  📊 Checking {symbol}...")
            
            # Get data counts
            price_data = self.dm.get_stock_prices(symbol, '2020-01-01', '2025-12-31')
            eps_data = self.dm.get_stock_eps(symbol, '2020-01-01', '2025-12-31')
            pe_data = self.dm.get_stock_pe_ratios(symbol, '2020-01-01', '2025-12-31')
            peg_data = self.dm.get_stock_peg_ratios(symbol, '2020-01-01', '2025-12-31')
            
            verification[symbol] = {
                'price_records': len(price_data),
                'eps_records': len(eps_data),
                'pe_records': len(pe_data),
                'peg_records': len(peg_data)
            }
            
            print(f"    📈 Price: {verification[symbol]['price_records']}, "
                  f"EPS: {verification[symbol]['eps_records']}, "
                  f"P/E: {verification[symbol]['pe_records']}, "
                  f"PEG: {verification[symbol]['peg_records']}")
        
        return verification

if __name__ == "__main__":
    print("🚀 Bulk Data Loader - Loading All Stocks")
    print("=" * 80)
    
    # Initialize bulk loader
    loader = BulkDataLoader(batch_size=5, delay_between_batches=3.0)
    
    # Load data for all stocks (skip existing ones)
    results = loader.load_all_stocks_data(years_back=None, skip_existing=True)
    
    # Verify results
    print("\n" + "=" * 80)
    verification = loader.verify_data_loading()
    
    print("\n" + "=" * 80)
    print("✅ Bulk data loading complete!")
    print(f"📊 Total stocks processed: {len(results)}")
    print(f"✅ Successful: {sum(1 for success in results.values() if success)}")
    print(f"❌ Failed: {sum(1 for success in results.values() if not success)}")

