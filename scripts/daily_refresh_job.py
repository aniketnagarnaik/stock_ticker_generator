"""
Daily Stock Data Refresh Job for Render
Runs daily after market close to update stock data in database
"""

import os
import sys
import requests
import time
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from publisher.data_publisher import DataPublisher
from database.database import db_manager

def refresh_stock_data():
    """Refresh stock data using current database architecture"""
    
    print(f"🔄 Daily Stock Data Refresh Job - {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Initialize data publisher
    data_publisher = DataPublisher()
    
    print("📊 Checking current database status...")
    try:
        # Check database connection
        session = db_manager.get_session()
        session.close()
        print("   ✅ Database connection successful")
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False
    
    print(f"\n🔄 Starting daily refresh...")
    
    try:
        print("📡 Fetching fresh stock data and updating database...")
        print("   (This may take 10-15 minutes due to rate limiting)")
        
        # Use the current data publisher to fetch and store data
        success, successful_count, failed_count = data_publisher.publish_all_stocks()
        
        if success:
            print(f"✅ Database updated successfully!")
            print(f"   📊 Successful: {successful_count} stocks")
            print(f"   ❌ Failed: {failed_count} stocks")
            return True
        else:
            print(f"❌ Failed to update database")
            print(f"   📊 Successful: {successful_count} stocks")
            print(f"   ❌ Failed: {failed_count} stocks")
            return False
            
    except Exception as e:
        print(f"❌ Error during refresh: {e}")
        import traceback
        traceback.print_exc()
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
    """Check the final database status"""
    
    print(f"\n📊 Final Database Status:")
    print("-" * 30)
    
    try:
        session = db_manager.get_session()
        
        # Count stocks in database
        from database.models import Stock
        stock_count = session.query(Stock).count()
        
        # Get latest refresh log
        from database.models import RefreshLog
        latest_log = session.query(RefreshLog).order_by(RefreshLog.started_at.desc()).first()
        
        print(f"✅ Database connection: Working")
        print(f"✅ Stock count: {stock_count}")
        if latest_log:
            print(f"✅ Last refresh: {latest_log.started_at}")
            print(f"✅ Last status: {latest_log.status}")
        else:
            print(f"✅ Last refresh: No previous refresh found")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"❌ Error checking database status: {e}")
        return False

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
            print(f"   ✅ Stock data updated in database")
            print(f"   ✅ Web app can now serve fresh data")
            return 0
        else:
            print(f"\n⚠️  Job completed but database status check failed")
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
