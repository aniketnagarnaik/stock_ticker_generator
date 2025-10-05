"""
Daily Stock Data Refresh Script
Runs daily to update the stock data cache
Can be used with Render cron jobs or GitHub Actions
"""

import os
import sys
import requests
import time
from datetime import datetime

def refresh_stock_cache():
    """Refresh the stock data cache by calling the refresh endpoint"""
    
    print(f"🔄 Daily Stock Data Refresh - {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Get the base URL - try environment variable first, then default to localhost
    base_url = os.environ.get('STOCK_APP_URL', 'http://localhost:5000')
    
    print(f"📡 Calling refresh endpoint: {base_url}/api/refresh")
    
    try:
        # Call the refresh endpoint
        response = requests.post(f"{base_url}/api/refresh", timeout=1800)  # 30 minute timeout
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Refresh successful!")
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Stock count: {data.get('count', 0)}")
            print(f"   Cache updated: {data.get('cache_updated', False)}")
            return True
        else:
            print(f"❌ Refresh failed with status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Request timed out after 30 minutes")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 Connection error - is the app running at {base_url}?")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_cache_status():
    """Check the current cache status"""
    
    print(f"\n📊 Checking Cache Status")
    print("-" * 30)
    
    base_url = os.environ.get('STOCK_APP_URL', 'http://localhost:5000')
    
    try:
        response = requests.get(f"{base_url}/api/cache/status", timeout=30)
        
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Cache Status:")
            print(f"   Exists: {status.get('cache_exists', False)}")
            print(f"   Valid: {status.get('cache_valid', False)}")
            print(f"   Last Updated: {status.get('last_updated', 'Unknown')}")
            print(f"   Stock Count: {status.get('stock_count', 0)}")
            print(f"   Age: {status.get('age_hours', 0):.1f} hours")
            print(f"   File Size: {status.get('cache_file_size', 0)} bytes")
            return True
        else:
            print(f"❌ Failed to get cache status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking cache status: {e}")
        return False

def main():
    """Main function"""
    
    print("🚀 Stock Data Daily Refresh Script")
    print("=" * 60)
    
    # Check if we should just check status
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        return check_cache_status()
    
    # Perform the refresh
    success = refresh_stock_cache()
    
    if success:
        print(f"\n✅ Daily refresh completed successfully!")
        
        # Wait a moment then check status
        print(f"\n⏳ Waiting 5 seconds before checking status...")
        time.sleep(5)
        check_cache_status()
        
        return 0
    else:
        print(f"\n❌ Daily refresh failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
