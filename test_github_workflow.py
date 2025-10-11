#!/usr/bin/env python3
"""
Test script to simulate GitHub Actions workflow
"""

import requests
import json
import os
from datetime import datetime
import pytz

def test_refresh_endpoint():
    """Test the /api/refresh endpoint"""
    
    # Get the app URL from environment or use localhost
    app_url = os.getenv('RENDER_APP_URL', 'http://localhost:5000')
    refresh_url = f"{app_url}/api/refresh"
    
    print(f"🧪 Testing GitHub Actions Workflow")
    print(f"📡 App URL: {app_url}")
    print(f"🔄 Refresh URL: {refresh_url}")
    print(f"⏰ Current time: {datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%d %H:%M:%S PT')}")
    print("-" * 60)
    
    try:
        # Test the refresh endpoint
        print("🚀 Sending POST request to /api/refresh...")
        response = requests.post(refresh_url, timeout=300)  # 5 minute timeout
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"📈 Message: {data.get('message', 'No message')}")
            print(f"🎯 Successful: {data.get('successful_count', 0)}")
            print(f"❌ Failed: {data.get('failed_count', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 'No timestamp')}")
        else:
            print("❌ FAILED!")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION ERROR!")
        print("💡 Make sure your Flask app is running:")
        print("   python3 app_new.py")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT ERROR!")
        print("💡 The refresh took longer than 5 minutes")
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_health_endpoint():
    """Test the /api/health endpoint"""
    
    app_url = os.getenv('RENDER_APP_URL', 'http://localhost:5000')
    health_url = f"{app_url}/api/health"
    
    print(f"\n🏥 Testing Health Endpoint")
    print(f"📡 Health URL: {health_url}")
    print("-" * 40)
    
    try:
        response = requests.get(health_url, timeout=10)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ App is healthy!")
            print(f"📈 Stock count: {data.get('stock_count', 0)}")
            print(f"⏰ Timestamp: {data.get('timestamp', 'No timestamp')}")
        else:
            print("❌ App is unhealthy!")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    print("🔍 GitHub Actions Workflow Test")
    print("=" * 50)
    
    # Test health endpoint first
    test_health_endpoint()
    
    # Test refresh endpoint
    test_refresh_endpoint()
    
    print("\n" + "=" * 50)
    print("💡 GitHub Actions will run this workflow:")
    print("   1. Check app health")
    print("   2. Trigger /api/refresh endpoint")
    print("   3. Parse JSON response")
    print("   4. Report success/failure")
    print("   5. Send notifications on failure")
