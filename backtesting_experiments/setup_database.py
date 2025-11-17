#!/usr/bin/env python3
"""
PostgreSQL Tables for Momentum Trading System
Creates all necessary tables for the modular momentum trading system
"""

import os
import sys
sys.path.append('..')

from database.database import db_manager
from sqlalchemy import text

def create_momentum_tables():
    """Create all tables for the momentum trading system"""
    
    print("🏗️ Creating PostgreSQL tables for Momentum Trading System...")
    
    # Raw data tables
    raw_data_tables = [
        """
        CREATE TABLE IF NOT EXISTS stock_prices (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            price_date DATE NOT NULL,
            open_price DECIMAL(10,4),
            high_price DECIMAL(10,4),
            low_price DECIMAL(10,4),
            close_price DECIMAL(10,4),
            volume BIGINT,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, price_date)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS stock_eps (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            eps_date DATE NOT NULL,
            eps_value DECIMAL(10,4),
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, eps_date)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS stock_pe_ratios (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            pe_date DATE NOT NULL,
            pe_value DECIMAL(10,4),
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, pe_date)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS stock_peg_ratios (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            peg_date DATE NOT NULL,
            peg_value DECIMAL(10,4),
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, peg_date)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS spy_data (
            id SERIAL PRIMARY KEY,
            spy_date DATE NOT NULL,
            open_price DECIMAL(10,4),
            high_price DECIMAL(10,4),
            low_price DECIMAL(10,4),
            close_price DECIMAL(10,4),
            volume BIGINT,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(spy_date)
        );
        """
    ]
    
    # Processed data tables
    processed_data_tables = [
        """
        CREATE TABLE IF NOT EXISTS momentum_scores (
            id SERIAL PRIMARY KEY,
            symbol VARCHAR(10) NOT NULL,
            calculation_date DATE NOT NULL,
            rs_vs_spy DECIMAL(8,4),
            eps_momentum DECIMAL(8,4),
            price_momentum DECIMAL(8,4),
            pe_momentum DECIMAL(8,4),
            volume_momentum DECIMAL(8,4),
            combined_score DECIMAL(8,4),
            rank INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(symbol, calculation_date)
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id SERIAL PRIMARY KEY,
            snapshot_date DATE NOT NULL,
            portfolio_value DECIMAL(15,2),
            cash DECIMAL(15,2),
            positions JSONB,
            rebalance_reason VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS backtest_results (
            id SERIAL PRIMARY KEY,
            strategy_name VARCHAR(50) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            total_return DECIMAL(8,4),
            annual_return DECIMAL(8,4),
            volatility DECIMAL(8,4),
            sharpe_ratio DECIMAL(8,4),
            max_drawdown DECIMAL(8,4),
            win_rate DECIMAL(8,4),
            alpha DECIMAL(8,4),
            beta DECIMAL(8,4),
            results_data JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
    ]
    
    # Create indexes for performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date ON stock_prices(symbol, price_date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_eps_symbol_date ON stock_eps(symbol, eps_date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_pe_symbol_date ON stock_pe_ratios(symbol, pe_date);",
        "CREATE INDEX IF NOT EXISTS idx_stock_peg_symbol_date ON stock_peg_ratios(symbol, peg_date);",
        "CREATE INDEX IF NOT EXISTS idx_spy_data_date ON spy_data(spy_date);",
        "CREATE INDEX IF NOT EXISTS idx_momentum_scores_date ON momentum_scores(calculation_date);",
        "CREATE INDEX IF NOT EXISTS idx_momentum_scores_symbol ON momentum_scores(symbol);",
        "CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_date ON portfolio_snapshots(snapshot_date);",
        "CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy ON backtest_results(strategy_name);"
    ]
    
    session = db_manager.get_session()
    try:
        # Create raw data tables
        print("📊 Creating raw data tables...")
        for table_sql in raw_data_tables:
            session.execute(text(table_sql))
        
        # Create processed data tables
        print("⚙️ Creating processed data tables...")
        for table_sql in processed_data_tables:
            session.execute(text(table_sql))
        
        # Create indexes
        print("🔍 Creating indexes...")
        for index_sql in indexes:
            session.execute(text(index_sql))
        
        session.commit()
        print("✅ All tables created successfully!")
        
        # Show table summary
        print("\n📋 Created Tables:")
        print("Raw Data Tables:")
        print("  - stock_prices")
        print("  - stock_eps")
        print("  - stock_pe_ratios")
        print("  - stock_peg_ratios")
        print("  - spy_data")
        print("\nProcessed Data Tables:")
        print("  - momentum_scores")
        print("  - portfolio_snapshots")
        print("  - backtest_results")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def drop_momentum_tables():
    """Drop all momentum trading tables (for testing)"""
    
    print("🗑️ Dropping momentum trading tables...")
    
    tables_to_drop = [
        "backtest_results",
        "portfolio_snapshots", 
        "momentum_scores",
        "spy_data",
        "stock_peg_ratios",
        "stock_pe_ratios",
        "stock_eps",
        "stock_prices"
    ]
    
    session = db_manager.get_session()
    try:
        for table in tables_to_drop:
            session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
        
        session.commit()
        print("✅ All tables dropped successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def show_table_info():
    """Show information about created tables"""
    
    print("\n📊 Table Information:")
    
    tables_info = [
        ("stock_prices", "Raw stock price data"),
        ("stock_eps", "Raw EPS data"),
        ("stock_pe_ratios", "Raw P/E ratio data"),
        ("stock_peg_ratios", "Raw PEG ratio data"),
        ("spy_data", "SPY benchmark data"),
        ("momentum_scores", "Calculated momentum scores"),
        ("portfolio_snapshots", "Portfolio state snapshots"),
        ("backtest_results", "Backtesting results")
    ]
    
    session = db_manager.get_session()
    try:
        for table_name, description in tables_info:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name};"))
                count = result.fetchone()[0]
                print(f"  {table_name:<20} - {description:<30} ({count} records)")
            except Exception as e:
                print(f"  {table_name:<20} - {description:<30} (Error: {e})")
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Momentum Trading System - Database Setup")
    print("=" * 60)
    
    # Create tables
    if create_momentum_tables():
        show_table_info()
    
    print("\n" + "=" * 60)
    print("✅ Database setup complete!")
