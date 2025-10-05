"""
Daily Stock Data Refresh Job for Render
Runs daily after market close to update stock data cache
"""

import os
import sys
import requests
import time
import json
from datetime import datetime
from cache_manager import StockCacheManager
from stock_data import StockData

def refresh_stock_data():
    """Refresh stock data with optimized rate limiting"""
    
    print(f"🔄 Daily Stock Data Refresh Job - {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Initialize cache manager
    cache_manager = StockCacheManager()
    
    print("📊 Checking current cache status...")
    status = cache_manager.get_cache_status()
    print(f"   Cache exists: {status['cache_exists']}")
    print(f"   Cache valid: {status['cache_valid']}")
    print(f"   Last updated: {status.get('last_updated', 'Never')}")
    print(f"   Age: {status.get('age_hours', 0):.1f} hours")
    
    # Force refresh regardless of cache age (daily job)
    print(f"\n🔄 Starting daily refresh (forced)...")
    
    try:
        # Use optimized stock data fetcher
        stock_data = StockData(enable_monitoring=True)
        
        print("📡 Fetching fresh stock data from Yahoo Finance...")
        print("   (This may take 10-15 minutes due to rate limiting)")
        
        fresh_data = stock_data.get_all_stocks()
        
        if not fresh_data:
            print("❌ Failed to fetch fresh data")
            return False
        
        print(f"✅ Successfully fetched {len(fresh_data)} stocks")
        
        # Save to cache
        print("💾 Saving data to cache...")
        success = cache_manager.save_to_cache(fresh_data)
        
        if success:
            print(f"✅ Cache updated successfully with {len(fresh_data)} stocks")
            
            # Print performance summary if available
            if hasattr(stock_data, 'print_performance_summary'):
                stock_data.print_performance_summary()
            
            return True
        else:
            print("❌ Failed to save data to cache")
            return False
            
    except Exception as e:
        print(f"❌ Error during refresh: {e}")
        return False

def notify_web_app():
    """Notify the web app that cache has been updated"""
    
    app_url = os.environ.get('STOCK_APP_URL', 'http://localhost:5000')
    
    print(f"\n📢 Notifying web app at {app_url}...")
    
    try:
        # Call the refresh endpoint to update the running app
        response = requests.post(f"{app_url}/api/refresh", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Web app notified successfully")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Stock count: {data.get('count', 0)}")
        else:
            print(f"⚠️  Web app notification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"⚠️  Could not notify web app: {e}")
        print(f"   (This is normal if the web app is not running)")

def check_final_status():
    """Check the final cache status"""
    
    print(f"\n📊 Final Cache Status:")
    print("-" * 30)
    
    cache_manager = StockCacheManager()
    status = cache_manager.get_cache_status()
    
    print(f"✅ Cache exists: {status['cache_exists']}")
    print(f"✅ Cache valid: {status['cache_valid']}")
    print(f"✅ Last updated: {status.get('last_updated', 'Unknown')}")
    print(f"✅ Stock count: {status.get('stock_count', 0)}")
    print(f"✅ Age: {status.get('age_hours', 0):.1f} hours")
    print(f"✅ File size: {status.get('cache_file_size', 0)} bytes")
    
    return status['cache_valid']

def main():
    """Main function for the daily refresh job"""
    
    print("🚀 Stock Data Daily Refresh Job")
    print("=" * 60)
    print(f"🕐 Started at: {datetime.now().isoformat()}")
    print(f"🌍 Environment: {os.environ.get('RENDER', 'Local')}")
    print(f"📊 App URL: {os.environ.get('STOCK_APP_URL', 'Not set')}")
    print(f"⏰ Scheduled: Daily at 8 PM ET (1 AM UTC)")
    
    try:
        # Step 1: Refresh stock data
        success = refresh_stock_data()
        
        if not success:
            print(f"\n❌ Daily refresh job failed!")
            return 1
        
        # Step 2: Notify web app (optional)
        notify_web_app()
        
        # Step 3: Check final status
        final_status = check_final_status()
        
        if final_status:
            print(f"\n🎉 Daily refresh job completed successfully!")
            print(f"   ✅ Stock data updated and cached")
            print(f"   ✅ Web app can now serve fresh data")
            return 0
        else:
            print(f"\n⚠️  Job completed but cache status is invalid")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error in daily refresh job: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        print(f"\n🕐 Job completed at: {datetime.now().isoformat()}")
        print("=" * 60)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
