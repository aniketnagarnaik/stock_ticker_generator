#!/usr/bin/env python3
"""
PostgreSQL Data Manager for Momentum Trading System
Handles all data operations using PostgreSQL as the single source of truth
"""

import os
import sys
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
import json

sys.path.append('..')
from database.database import db_manager

class PostgresDataManager:
    """Manages all data operations using PostgreSQL"""
    
    def __init__(self):
        self.db = db_manager
        print("📊 PostgresDataManager initialized")
    
    def _get_session(self):
        """Get database session"""
        return self.db.get_session()
    
    # ==================== RAW DATA OPERATIONS ====================
    
    def load_stock_prices(self, symbol: str, price_data: pd.DataFrame) -> bool:
        """Load stock price data to PostgreSQL"""
        session = self._get_session()
        try:
            for _, row in price_data.iterrows():
                session.execute(text("""
                    INSERT INTO stock_prices (symbol, price_date, open_price, high_price, low_price, close_price, volume)
                    VALUES (:symbol, :price_date, :open_price, :high_price, :low_price, :close_price, :volume)
                    ON CONFLICT (symbol, price_date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume
                """), {
                    'symbol': symbol,
                    'price_date': row['date'],
                    'open_price': row.get('open'),
                    'high_price': row.get('high'),
                    'low_price': row.get('low'),
                    'close_price': row.get('close'),
                    'volume': row.get('volume')
                })
            
            session.commit()
            print(f"✅ Loaded {len(price_data)} price records for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading price data for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def load_stock_eps(self, symbol: str, eps_data: pd.DataFrame) -> bool:
        """Load EPS data to PostgreSQL"""
        session = self._get_session()
        try:
            for _, row in eps_data.iterrows():
                session.execute(text("""
                    INSERT INTO stock_eps (symbol, eps_date, eps_value)
                    VALUES (:symbol, :eps_date, :eps_value)
                    ON CONFLICT (symbol, eps_date) DO UPDATE SET eps_value = EXCLUDED.eps_value
                """), {
                    'symbol': symbol,
                    'eps_date': row['date'],
                    'eps_value': row.get('eps')
                })
            
            session.commit()
            print(f"✅ Loaded {len(eps_data)} EPS records for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading EPS data for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def load_stock_pe_ratios(self, symbol: str, pe_data: pd.DataFrame) -> bool:
        """Load P/E ratio data to PostgreSQL"""
        session = self._get_session()
        try:
            for _, row in pe_data.iterrows():
                session.execute(text("""
                    INSERT INTO stock_pe_ratios (symbol, pe_date, pe_value)
                    VALUES (:symbol, :pe_date, :pe_value)
                    ON CONFLICT (symbol, pe_date) DO UPDATE SET pe_value = EXCLUDED.pe_value
                """), {
                    'symbol': symbol,
                    'pe_date': row['date'],
                    'pe_value': row.get('pe')
                })
            
            session.commit()
            print(f"✅ Loaded {len(pe_data)} P/E records for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading P/E data for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def load_stock_peg_ratios(self, symbol: str, peg_data: pd.DataFrame) -> bool:
        """Load PEG ratio data to PostgreSQL"""
        session = self._get_session()
        try:
            for _, row in peg_data.iterrows():
                session.execute(text("""
                    INSERT INTO stock_peg_ratios (symbol, peg_date, peg_value)
                    VALUES (:symbol, :peg_date, :peg_value)
                    ON CONFLICT (symbol, peg_date) DO UPDATE SET peg_value = EXCLUDED.peg_value
                """), {
                    'symbol': symbol,
                    'peg_date': row['date'],
                    'peg_value': row.get('peg')
                })
            
            session.commit()
            print(f"✅ Loaded {len(peg_data)} PEG records for {symbol}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading PEG data for {symbol}: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def load_spy_data(self, spy_data: pd.DataFrame) -> bool:
        """Load SPY benchmark data to PostgreSQL"""
        session = self._get_session()
        try:
            for _, row in spy_data.iterrows():
                session.execute(text("""
                    INSERT INTO spy_data (spy_date, open_price, high_price, low_price, close_price, volume)
                    VALUES (:spy_date, :open_price, :high_price, :low_price, :close_price, :volume)
                    ON CONFLICT (spy_date) DO UPDATE SET
                        open_price = EXCLUDED.open_price,
                        high_price = EXCLUDED.high_price,
                        low_price = EXCLUDED.low_price,
                        close_price = EXCLUDED.close_price,
                        volume = EXCLUDED.volume
                """), {
                    'spy_date': row['date'],
                    'open_price': row.get('open'),
                    'high_price': row.get('high'),
                    'low_price': row.get('low'),
                    'close_price': row.get('close'),
                    'volume': row.get('volume')
                })
            
            session.commit()
            print(f"✅ Loaded {len(spy_data)} SPY records")
            return True
            
        except Exception as e:
            print(f"❌ Error loading SPY data: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    # ==================== DATA RETRIEVAL ====================
    
    def get_stock_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get stock price data from PostgreSQL"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT price_date as date, open_price as open, high_price as high, 
                       low_price as low, close_price as close, volume
                FROM stock_prices 
                WHERE symbol = :symbol AND price_date BETWEEN :start_date AND :end_date
                ORDER BY price_date
            """), {'symbol': symbol, 'start_date': start_date, 'end_date': end_date})
            
            data = result.fetchall()
            if data:
                df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error getting price data for {symbol}: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_stock_eps(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get EPS data from PostgreSQL"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT eps_date as date, eps_value as eps
                FROM stock_eps 
                WHERE symbol = :symbol AND eps_date BETWEEN :start_date AND :end_date
                ORDER BY eps_date
            """), {'symbol': symbol, 'start_date': start_date, 'end_date': end_date})
            
            data = result.fetchall()
            if data:
                df = pd.DataFrame(data, columns=['date', 'eps'])
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error getting EPS data for {symbol}: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_stock_pe_ratios(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get P/E ratio data from PostgreSQL"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT pe_date as date, pe_value as pe
                FROM stock_pe_ratios 
                WHERE symbol = :symbol AND pe_date BETWEEN :start_date AND :end_date
                ORDER BY pe_date
            """), {'symbol': symbol, 'start_date': start_date, 'end_date': end_date})
            
            data = result.fetchall()
            if data:
                df = pd.DataFrame(data, columns=['date', 'pe'])
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error getting P/E data for {symbol}: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_stock_peg_ratios(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get PEG ratio data from PostgreSQL"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT peg_date as date, peg_value as peg
                FROM stock_peg_ratios 
                WHERE symbol = :symbol AND peg_date BETWEEN :start_date AND :end_date
                ORDER BY peg_date
            """), {'symbol': symbol, 'start_date': start_date, 'end_date': end_date})
            
            data = result.fetchall()
            if data:
                df = pd.DataFrame(data, columns=['date', 'peg'])
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error getting PEG data for {symbol}: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    def get_spy_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get SPY benchmark data from PostgreSQL"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT spy_date as date, open_price as open, high_price as high, 
                       low_price as low, close_price as close, volume
                FROM spy_data 
                WHERE spy_date BETWEEN :start_date AND :end_date
                ORDER BY spy_date
            """), {'start_date': start_date, 'end_date': end_date})
            
            data = result.fetchall()
            if data:
                df = pd.DataFrame(data, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"❌ Error getting SPY data: {e}")
            return pd.DataFrame()
        finally:
            session.close()
    
    # ==================== MOMENTUM SCORES ====================
    
    def save_momentum_scores(self, scores: Dict[str, Dict], calculation_date: str) -> bool:
        """Save calculated momentum scores to PostgreSQL"""
        session = self._get_session()
        try:
            for symbol, score_data in scores.items():
                # Convert all values to Python native types to avoid numpy type issues
                params = {
                    'symbol': symbol,
                    'calculation_date': calculation_date,
                    'rs_vs_spy': float(score_data.get('rs_vs_spy', 0)),
                    'eps_momentum': float(score_data.get('eps_momentum', 0)),
                    'price_momentum': float(score_data.get('price_momentum', 0)),
                    'pe_momentum': float(score_data.get('pe_momentum', 0)),
                    'volume_momentum': float(score_data.get('volume_momentum', 0)),
                    'combined_score': float(score_data.get('combined_score', 0)),
                    'rank': int(score_data.get('rank', 0))
                }
                
                session.execute(text("""
                    INSERT INTO momentum_scores (symbol, calculation_date, rs_vs_spy, eps_momentum, 
                                               price_momentum, pe_momentum, volume_momentum, combined_score, rank)
                    VALUES (:symbol, :calculation_date, :rs_vs_spy, :eps_momentum, 
                           :price_momentum, :pe_momentum, :volume_momentum, :combined_score, :rank)
                    ON CONFLICT (symbol, calculation_date) DO UPDATE SET
                        rs_vs_spy = EXCLUDED.rs_vs_spy,
                        eps_momentum = EXCLUDED.eps_momentum,
                        price_momentum = EXCLUDED.price_momentum,
                        pe_momentum = EXCLUDED.pe_momentum,
                        volume_momentum = EXCLUDED.volume_momentum,
                        combined_score = EXCLUDED.combined_score,
                        rank = EXCLUDED.rank
                """), params)
            
            session.commit()
            print(f"✅ Saved momentum scores for {len(scores)} stocks on {calculation_date}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving momentum scores: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_momentum_scores(self, calculation_date: str) -> Dict[str, Dict]:
        """Get momentum scores from PostgreSQL"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT symbol, rs_vs_spy, eps_momentum, price_momentum, pe_momentum, 
                       volume_momentum, combined_score, rank
                FROM momentum_scores 
                WHERE calculation_date = :calculation_date
                ORDER BY combined_score DESC
            """), {'calculation_date': calculation_date})
            
            scores = {}
            for row in result.fetchall():
                scores[row[0]] = {
                    'rs_vs_spy': row[1],
                    'eps_momentum': row[2],
                    'price_momentum': row[3],
                    'pe_momentum': row[4],
                    'volume_momentum': row[5],
                    'combined_score': row[6],
                    'rank': row[7]
                }
            
            return scores
            
        except Exception as e:
            print(f"❌ Error getting momentum scores: {e}")
            return {}
        finally:
            session.close()
    
    # ==================== UTILITY METHODS ====================
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available stock symbols"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol
            """))
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            print(f"❌ Error getting available symbols: {e}")
            return []
        finally:
            session.close()
    
    def get_data_date_range(self, symbol: str) -> Tuple[Optional[str], Optional[str]]:
        """Get date range for a symbol's data"""
        session = self._get_session()
        try:
            result = session.execute(text("""
                SELECT MIN(price_date), MAX(price_date) 
                FROM stock_prices 
                WHERE symbol = :symbol
            """), {'symbol': symbol})
            
            row = result.fetchone()
            if row and row[0] and row[1]:
                return str(row[0]), str(row[1])
            else:
                return None, None
                
        except Exception as e:
            print(f"❌ Error getting date range for {symbol}: {e}")
            return None, None
        finally:
            session.close()
    
    def clear_data(self, symbol: str = None) -> bool:
        """Clear data for a specific symbol or all data"""
        session = self._get_session()
        try:
            if symbol:
                tables = ['stock_prices', 'stock_eps', 'stock_pe_ratios', 'stock_peg_ratios']
                for table in tables:
                    session.execute(text(f"DELETE FROM {table} WHERE symbol = :symbol"), {'symbol': symbol})
                print(f"✅ Cleared data for {symbol}")
            else:
                tables = ['backtest_results', 'portfolio_snapshots', 'momentum_scores', 
                         'spy_data', 'stock_peg_ratios', 'stock_pe_ratios', 'stock_eps', 'stock_prices']
                for table in tables:
                    session.execute(text(f"DELETE FROM {table}"))
                print("✅ Cleared all data")
            
            session.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            session.rollback()
            return False
        finally:
            session.close()

if __name__ == "__main__":
    # Test the data manager
    print("🧪 Testing PostgresDataManager...")
    
    dm = PostgresDataManager()
    
    # Test getting available symbols
    symbols = dm.get_available_symbols()
    print(f"📊 Available symbols: {symbols}")
    
    # Test getting date range for first symbol
    if symbols:
        symbol = symbols[0]
        start_date, end_date = dm.get_data_date_range(symbol)
        print(f"📅 Date range for {symbol}: {start_date} to {end_date}")
    
    print("✅ PostgresDataManager test complete!")