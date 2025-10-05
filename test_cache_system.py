"""
Test the caching system
Verifies that cache loading/saving works correctly
"""

from cache_manager import StockCacheManager
import json
import os

def test_cache_system():
    """Test the complete caching system"""
    
    print("🧪 Testing Stock Cache System")
    print("=" * 50)
    
    # Create cache manager
    cache_manager = StockCacheManager()
    
    # Test 1: Clear any existing cache
    print("\n1️⃣ Clearing existing cache...")
    cache_manager.clear_cache()
    
    # Test 2: Check initial status
    print("\n2️⃣ Checking initial cache status...")
    status = cache_manager.get_cache_status()
    print(f"   Cache exists: {status['cache_exists']}")
    print(f"   Cache valid: {status['cache_valid']}")
    
    # Test 3: Try to load from empty cache
    print("\n3️⃣ Trying to load from empty cache...")
    cached_data = cache_manager.load_from_cache()
    if cached_data:
        print(f"   ❌ Unexpected: Loaded {len(cached_data)} stocks from empty cache")
    else:
        print(f"   ✅ Correctly returned None for empty cache")
    
    # Test 4: Create sample data and save to cache
    print("\n4️⃣ Creating sample data and saving to cache...")
    sample_data = [
        {
            'symbol': 'AAPL',
            'company_name': 'Apple Inc.',
            'market_cap': 3000000000000,
            'price': 150.0,
            'eps': 6.0,
            'sector': 'Technology'
        },
        {
            'symbol': 'MSFT',
            'company_name': 'Microsoft Corporation',
            'market_cap': 2500000000000,
            'price': 300.0,
            'eps': 10.0,
            'sector': 'Technology'
        }
    ]
    
    success = cache_manager.save_to_cache(sample_data)
    if success:
        print(f"   ✅ Successfully saved {len(sample_data)} stocks to cache")
    else:
        print(f"   ❌ Failed to save to cache")
        return False
    
    # Test 5: Check cache status after saving
    print("\n5️⃣ Checking cache status after saving...")
    status = cache_manager.get_cache_status()
    print(f"   Cache exists: {status['cache_exists']}")
    print(f"   Cache valid: {status['cache_valid']}")
    print(f"   Stock count: {status['stock_count']}")
    print(f"   File size: {status['cache_file_size']} bytes")
    
    # Test 6: Load from cache
    print("\n6️⃣ Loading data from cache...")
    loaded_data = cache_manager.load_from_cache()
    if loaded_data:
        print(f"   ✅ Successfully loaded {len(loaded_data)} stocks from cache")
        print(f"   First stock: {loaded_data[0]['symbol']} - {loaded_data[0]['company_name']}")
    else:
        print(f"   ❌ Failed to load from cache")
        return False
    
    # Test 7: Verify data integrity
    print("\n7️⃣ Verifying data integrity...")
    if len(loaded_data) == len(sample_data):
        print(f"   ✅ Stock count matches: {len(loaded_data)}")
    else:
        print(f"   ❌ Stock count mismatch: {len(loaded_data)} vs {len(sample_data)}")
        return False
    
    if loaded_data[0]['symbol'] == sample_data[0]['symbol']:
        print(f"   ✅ Data integrity verified")
    else:
        print(f"   ❌ Data integrity failed")
        return False
    
    # Test 8: Test cache expiration (simulate old cache)
    print("\n8️⃣ Testing cache expiration...")
    # Manually modify metadata to make cache appear old
    try:
        with open(cache_manager.cache_metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Set last_updated to 25 hours ago
        from datetime import datetime, timedelta
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        metadata['last_updated'] = old_time
        
        with open(cache_manager.cache_metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        print(f"   📅 Set cache timestamp to 25 hours ago")
        
        # Check if cache is now invalid
        is_valid = cache_manager.is_cache_valid()
        if not is_valid:
            print(f"   ✅ Cache correctly identified as expired")
        else:
            print(f"   ❌ Cache should be expired but shows as valid")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing cache expiration: {e}")
        return False
    
    # Test 9: Clean up
    print("\n9️⃣ Cleaning up test files...")
    cache_manager.clear_cache()
    
    # Verify cleanup
    status = cache_manager.get_cache_status()
    if not status['cache_exists']:
        print(f"   ✅ Cache successfully cleared")
    else:
        print(f"   ❌ Cache still exists after cleanup")
        return False
    
    print(f"\n🎉 All cache system tests passed!")
    return True

if __name__ == "__main__":
    success = test_cache_system()
    if success:
        print(f"\n✅ Cache system is working correctly!")
        exit(0)
    else:
        print(f"\n❌ Cache system tests failed!")
        exit(1)
