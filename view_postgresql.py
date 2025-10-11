#!/usr/bin/env python3
"""
PostgreSQL Database Viewer - Interactive tool to view stock data
"""

import os
import psycopg2
import json
from tabulate import tabulate

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def view_stocks():
    """View all stocks"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, company_name, 
                   ROUND(current_price::numeric, 2) as price,
                   ROUND((market_cap / 1000000000)::numeric, 1) as market_cap_b,
                   sector, industry
            FROM stocks 
            ORDER BY market_cap DESC
        """)
        
        rows = cur.fetchall()
        
        print("\n📈 STOCKS TABLE")
        print("=" * 80)
        
        headers = ["Symbol", "Company", "Price", "Market Cap (B)", "Sector", "Industry"]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def view_metrics():
    """View stock metrics"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT symbol, 
                   ROUND(eps_growth_qoq::numeric, 1) as eps_growth_qoq,
                   ROUND(eps_growth_yoy::numeric, 1) as eps_growth_yoy,
                   rs_spy, rs_sector,
                   ema_data
            FROM stock_metrics 
            ORDER BY symbol
        """)
        
        rows = cur.fetchall()
        
        print("\n📊 STOCK METRICS")
        print("=" * 100)
        
        for row in rows:
            symbol, eps_qoq, eps_yoy, rs_spy, rs_sector, ema_data = row
            print(f"\n{symbol}:")
            print(f"  EPS Growth: QoQ {eps_qoq}%, YoY {eps_yoy}%")
            print(f"  Relative Strength: SPY {rs_spy}, Sector {rs_sector}")
            
            if ema_data:
                ema_json = json.loads(ema_data)
                print(f"  EMAs: 9D {ema_json.get('D_9EMA', 'N/A'):.2f}, 21D {ema_json.get('D_21EMA', 'N/A'):.2f}, 50D {ema_json.get('D_50EMA', 'N/A'):.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def view_tables():
    """View all tables"""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        rows = cur.fetchall()
        
        print("\n🗄️  DATABASE TABLES")
        print("=" * 40)
        print(tabulate(rows, headers=["Table Name", "Columns"], tablefmt="grid"))
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

def main():
    """Main menu"""
    print("🗄️  POSTGRESQL DATABASE VIEWER")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. View Stocks")
        print("2. View Metrics") 
        print("3. View Tables")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            view_stocks()
        elif choice == '2':
            view_metrics()
        elif choice == '3':
            view_tables()
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
