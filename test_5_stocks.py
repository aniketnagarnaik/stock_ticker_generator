#!/usr/bin/env python3
"""
Test script to populate database with 5 stocks for local testing
"""

from publisher.data_publisher import DataPublisher
from publisher.yahoo_client import YahooFinanceClient

def test_5_stocks():
    """Test with 5 popular stocks"""
    
    # 5 popular stocks for testing
    test_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
    
    print("🚀 Testing with 5 stocks...")
    print(f"Symbols: {', '.join(test_symbols)}")
    
    # Initialize data publisher and yahoo client
    data_publisher = DataPublisher()
    yahoo_client = YahooFinanceClient()
    
    # Fetch data for these specific stocks
    fresh_data = []
    for symbol in test_symbols:
        print(f"📡 Fetching data for {symbol}...")
        stock_data = yahoo_client.get_stock_info(symbol)
        if stock_data:
            fresh_data.append(stock_data)
            print(f"✅ Got data for {symbol}")
        else:
            print(f"❌ Failed to get data for {symbol}")
    
    if not fresh_data:
        print("❌ Failed to fetch any data from Yahoo Finance")
        return
    
    # Publish data for these 5 stocks
    successful_count = 0
    failed_count = 0
    
    from database.database import db_manager
    session = db_manager.get_session()
    
    try:
        for stock_data in fresh_data:
            try:
                data_publisher._publish_single_stock(session, stock_data)
                successful_count += 1
                print(f"✅ Published {stock_data.get('symbol', 'unknown')}")
            except Exception as e:
                print(f"❌ Failed to publish {stock_data.get('symbol', 'unknown')}: {e}")
                failed_count += 1
        
        session.commit()
        success = successful_count > 0
    except Exception as e:
        session.rollback()
        print(f"❌ Database error: {e}")
        success = False
    finally:
        session.close()
    
    print(f"\n📊 Results:")
    print(f"✅ Successful: {successful_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"🎯 Overall: {'SUCCESS' if success else 'FAILED'}")
    
    if successful_count > 0:
        print(f"\n🎉 Database populated with {successful_count} stocks!")
        print("You can now run: python3 app_new.py")
    else:
        print("\n💥 No stocks were successfully added to database")

if __name__ == "__main__":
    test_5_stocks()
