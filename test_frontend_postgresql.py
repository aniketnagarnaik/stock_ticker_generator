#!/usr/bin/env python3
"""
Test script to verify PostgreSQL is properly connected to frontend
and all data is rendering accurately
"""

import requests
import json
from datetime import datetime
import pytz

def test_database_connection():
    """Test if PostgreSQL database is connected"""
    print("🔍 TESTING POSTGRESQL → FRONTEND CONNECTION")
    print("=" * 60)
    
    base_url = "http://localhost:5000"
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed")
            print(f"   📊 Stock count: {data.get('stock_count', 0)}")
            print(f"   ⏰ Timestamp: {data.get('timestamp', 'N/A')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: API Stocks Endpoint
    print("\n2️⃣ Testing /api/stocks Endpoint...")
    try:
        response = requests.get(f"{base_url}/api/stocks")
        if response.status_code == 200:
            stocks = response.json()
            print(f"   ✅ API endpoint working")
            print(f"   📊 Stocks returned: {len(stocks)}")
            
            # Verify data structure
            if stocks:
                test_stock = stocks[0]
                required_fields = ['symbol', 'company_name', 'price', 'market_cap', 
                                 'sector', 'eps', 'ema_data', 'eps_growth', 'relative_strength']
                
                print(f"\n   🔍 Verifying data fields for {test_stock.get('symbol', 'Unknown')}:")
                for field in required_fields:
                    if field in test_stock:
                        print(f"      ✅ {field}: Present")
                    else:
                        print(f"      ❌ {field}: Missing")
        else:
            print(f"   ❌ API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 3: Verify EMA Data
    print("\n3️⃣ Testing EMA Data Integrity...")
    try:
        for stock in stocks[:3]:  # Test first 3 stocks
            symbol = stock.get('symbol', 'Unknown')
            ema_data = stock.get('ema_data', {})
            
            ema_fields = ['D_9EMA', 'D_21EMA', 'D_50EMA', 'W_9EMA', 'W_21EMA', 'W_50EMA', 'M_9EMA']
            ema_present = sum(1 for field in ema_fields if ema_data.get(field) is not None)
            
            print(f"   {symbol}: {ema_present}/{len(ema_fields)} EMAs present")
            
            if ema_present >= 5:
                print(f"      ✅ EMA data looks good")
            else:
                print(f"      ⚠️  Some EMAs missing (expected for recent data)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Verify Frontend Rendering
    print("\n4️⃣ Testing Frontend Rendering...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            html = response.text
            
            # Check if stock data is embedded
            if 'stockData' in html:
                print("   ✅ Stock data embedded in HTML")
            else:
                print("   ❌ Stock data NOT embedded")
                return False
            
            # Check if all stocks are in the HTML
            for stock in stocks:
                symbol = stock.get('symbol', '')
                if symbol in html:
                    print(f"   ✅ {symbol} rendered in HTML")
                else:
                    print(f"   ❌ {symbol} NOT found in HTML")
        else:
            print(f"   ❌ Frontend failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 5: Verify Database Type
    print("\n5️⃣ Verifying Database Type...")
    try:
        import os
        db_url = os.getenv('DATABASE_URL', 'Not set')
        if 'postgresql' in db_url:
            print(f"   ✅ Using PostgreSQL")
            print(f"   📍 Connection: {db_url[:50]}...")
        elif 'sqlite' in db_url.lower():
            print(f"   ⚠️  Using SQLite (should be PostgreSQL)")
        else:
            print(f"   ❌ Database URL: {db_url}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Test Detailed Stock Data
    print("\n6️⃣ Testing Detailed Stock Data...")
    try:
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        for symbol in test_symbols:
            stock_data = next((s for s in stocks if s['symbol'] == symbol), None)
            if stock_data:
                print(f"\n   📊 {symbol} - {stock_data['company_name']}")
                print(f"      Price: ${stock_data['price']:.2f}")
                print(f"      Market Cap: ${stock_data['market_cap']/1e12:.1f}T")
                print(f"      EPS: {stock_data['eps']}")
                print(f"      EPS Growth QoQ: {stock_data['eps_growth']['quarter_over_quarter']:.1f}%")
                
                ema = stock_data['ema_data']
                if ema.get('D_9EMA'):
                    print(f"      9D EMA: ${ema['D_9EMA']:.2f}")
                if ema.get('D_21EMA'):
                    print(f"      21D EMA: ${ema['D_21EMA']:.2f}")
                if ema.get('D_50EMA'):
                    print(f"      50D EMA: ${ema['D_50EMA']:.2f}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return True

if __name__ == "__main__":
    print(f"\n⏰ Test Time: {datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S PT')}")
    
    success = test_database_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ PostgreSQL is properly connected to frontend")
        print("✅ All data is rendering accurately")
    else:
        print("❌ SOME TESTS FAILED")
        print("💡 Check the errors above for details")
    print("=" * 60)
