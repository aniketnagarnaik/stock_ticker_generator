#!/usr/bin/env python3
"""
Database Viewer - View tables and data in the stock ticker database
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.database import db_manager
from database.models import Stock, StockMetrics, RefreshLog

def view_stocks_table():
    """View stocks table"""
    session = db_manager.get_session()
    try:
        stocks = session.query(Stock).all()
        
        print(f"\n📈 STOCKS TABLE ({len(stocks)} records)")
        print("=" * 80)
        print(f"{'Symbol':<8} {'Company Name':<30} {'Price':<10} {'Market Cap':<12} {'Sector'}")
        print("-" * 80)
        
        for stock in stocks:
            market_cap_str = f"${stock.market_cap/1e9:.1f}B" if stock.market_cap else "N/A"
            print(f"{stock.symbol:<8} {stock.company_name[:29]:<30} ${stock.current_price:<9.2f} {market_cap_str:<12} {stock.sector}")
            
    finally:
        session.close()

def view_metrics_table():
    """View stock metrics table"""
    session = db_manager.get_session()
    try:
        metrics = session.query(StockMetrics).all()
        
        print(f"\n📊 STOCK METRICS TABLE ({len(metrics)} records)")
        print("=" * 100)
        print(f"{'Symbol':<8} {'EPS Growth':<12} {'RS vs SPY':<10} {'RS vs Sector':<12} {'D_9EMA':<10} {'D_21EMA':<10} {'D_50EMA'}")
        print("-" * 100)
        
        for metric in metrics:
            ema_data = metric.get_ema_data()
            eps_growth = f"{metric.eps_growth_qoq:.1f}%" if metric.eps_growth_qoq else "N/A"
            rs_spy = f"{metric.rs_spy:.1f}" if metric.rs_spy else "N/A"
            rs_sector = f"{metric.rs_sector:.1f}" if metric.rs_sector else "N/A"
            d9ema = f"{ema_data.get('D_9EMA', 0):.2f}" if ema_data.get('D_9EMA') else "N/A"
            d21ema = f"{ema_data.get('D_21EMA', 0):.2f}" if ema_data.get('D_21EMA') else "N/A"
            d50ema = f"{ema_data.get('D_50EMA', 0):.2f}" if ema_data.get('D_50EMA') else "N/A"
            
            print(f"{metric.symbol:<8} {eps_growth:<12} {rs_spy:<10} {rs_sector:<12} {d9ema:<10} {d21ema:<10} {d50ema}")
            
    finally:
        session.close()

def view_refresh_logs():
    """View refresh logs table"""
    session = db_manager.get_session()
    try:
        logs = session.query(RefreshLog).order_by(RefreshLog.started_at.desc()).all()
        
        print(f"\n🔄 REFRESH LOGS TABLE ({len(logs)} records)")
        print("=" * 80)
        print(f"{'Started':<20} {'Status':<10} {'Duration':<10} {'Success':<8} {'Failed':<8} {'Error'}")
        print("-" * 80)
        
        for log in logs:
            started_str = log.started_at.strftime("%m/%d %H:%M:%S") if log.started_at else "N/A"
            duration_str = f"{log.duration_seconds:.1f}s" if log.duration_seconds else "N/A"
            error_str = log.error_message[:20] + "..." if log.error_message and len(log.error_message) > 20 else (log.error_message or "")
            
            print(f"{started_str:<20} {log.status:<10} {duration_str:<10} {log.stocks_successful:<8} {log.stocks_failed:<8} {error_str}")
            
    finally:
        session.close()

def view_detailed_stock(symbol):
    """View detailed information for a specific stock"""
    session = db_manager.get_session()
    try:
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            print(f"❌ Stock {symbol} not found")
            return
            
        metrics = session.query(StockMetrics).filter(StockMetrics.symbol == symbol).first()
        
        print(f"\n📊 DETAILED VIEW: {symbol}")
        print("=" * 60)
        print(f"Company: {stock.company_name}")
        print(f"Sector: {stock.sector}")
        print(f"Industry: {stock.industry}")
        print(f"Current Price: ${stock.current_price:.2f}")
        print(f"Market Cap: ${stock.market_cap/1e9:.1f}B" if stock.market_cap else "Market Cap: N/A")
        print(f"EPS: {stock.eps}")
        print(f"Last Updated: {stock.last_updated}")
        
        if metrics:
            print(f"\n📈 METRICS:")
            print(f"EPS Growth (QoQ): {metrics.eps_growth_qoq:.1f}%" if metrics.eps_growth_qoq else "EPS Growth (QoQ): N/A")
            print(f"EPS Growth (YoY): {metrics.eps_growth_yoy:.1f}%" if metrics.eps_growth_yoy else "EPS Growth (YoY): N/A")
            print(f"RS vs SPY: {metrics.rs_spy:.1f}" if metrics.rs_spy else "RS vs SPY: N/A")
            print(f"RS vs Sector: {metrics.rs_sector:.1f}" if metrics.rs_sector else "RS vs Sector: N/A")
            
            ema_data = metrics.get_ema_data()
            if ema_data:
                print(f"\n📊 EMA VALUES:")
                for key, value in ema_data.items():
                    if value is not None:
                        print(f"{key}: {value:.2f}")
                    else:
                        print(f"{key}: N/A")
        else:
            print("\n❌ No metrics found for this stock")
            
    finally:
        session.close()

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "stocks":
            view_stocks_table()
        elif command == "metrics":
            view_metrics_table()
        elif command == "logs":
            view_refresh_logs()
        elif command == "detail" and len(sys.argv) > 2:
            symbol = sys.argv[2].upper()
            view_detailed_stock(symbol)
        else:
            print("❌ Unknown command. Available commands:")
            print("  python view_database.py stocks    - View stocks table")
            print("  python view_database.py metrics   - View metrics table")
            print("  python view_database.py logs      - View refresh logs")
            print("  python view_database.py detail AAPL - View detailed stock info")
    else:
        # Show all tables
        print("🗄️  STOCK TICKER DATABASE VIEWER")
        print("=" * 50)
        
        view_stocks_table()
        view_metrics_table()
        view_refresh_logs()
        
        print(f"\n💡 Use specific commands:")
        print(f"  python view_database.py stocks    - View stocks table only")
        print(f"  python view_database.py metrics   - View metrics table only")
        print(f"  python view_database.py logs      - View refresh logs only")
        print(f"  python view_database.py detail AAPL - View detailed AAPL info")

if __name__ == "__main__":
    main()
