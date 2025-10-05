"""
Stock Data Cache Manager
Handles saving and loading stock data to/from JSON cache files
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import pytz
from stock_data import StockData

class StockCacheManager:
    """Manages caching of stock data to improve performance"""
    
    def __init__(self, cache_file: str = "cache/stock_cache.json", max_age_hours: int = 24):
        self.cache_file = cache_file
        self.max_age_hours = max_age_hours
        self.cache_metadata_file = "cache/cache_metadata.json"
        self.pst = pytz.timezone('US/Pacific')
    
    def _get_cache_metadata(self) -> Dict:
        """Get cache metadata (last update time, etc.)"""
        try:
            if os.path.exists(self.cache_metadata_file):
                with open(self.cache_metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error reading cache metadata: {e}")
        
        return {
            'last_updated': None,
            'stock_count': 0,
            'cache_version': '1.0'
        }
    
    def _save_cache_metadata(self, metadata: Dict):
        """Save cache metadata"""
        try:
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving cache metadata: {e}")
    
    def is_cache_valid(self) -> bool:
        """Check if cache exists and is not expired"""
        try:
            # Check if cache file exists
            if not os.path.exists(self.cache_file):
                print("❌ Cache file does not exist")
                return False
            
            # Check cache age
            metadata = self._get_cache_metadata()
            if not metadata.get('last_updated'):
                print("❌ No cache timestamp found")
                return False
            
            # Handle both ISO format and PST format
            last_updated_str = metadata['last_updated']
            if 'PST' in last_updated_str:
                # Parse PST format: "2025-10-04 20:22 PST"
                last_updated = datetime.strptime(last_updated_str.replace(' PST', ''), '%Y-%m-%d %H:%M')
                last_updated = self.pst.localize(last_updated)
            else:
                # Parse ISO format
                last_updated = datetime.fromisoformat(last_updated_str)
                if last_updated.tzinfo is None:
                    last_updated = self.pst.localize(last_updated)
            
            age_hours = (datetime.now(self.pst) - last_updated).total_seconds() / 3600
            
            if age_hours > self.max_age_hours:
                print(f"❌ Cache expired ({age_hours:.1f} hours old, max: {self.max_age_hours} hours)")
                return False
            
            print(f"✅ Cache is valid ({age_hours:.1f} hours old)")
            return True
            
        except Exception as e:
            print(f"❌ Error checking cache validity: {e}")
            return False
    
    def load_from_cache(self) -> Optional[List[Dict]]:
        """Load stock data from cache file"""
        try:
            if not self.is_cache_valid():
                return None
            
            print(f"📂 Loading stock data from cache: {self.cache_file}")
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            metadata = self._get_cache_metadata()
            print(f"✅ Loaded {len(data)} stocks from cache (updated: {metadata.get('last_updated', 'unknown')})")
            
            return data
            
        except Exception as e:
            print(f"❌ Error loading from cache: {e}")
            return None
    
    def save_to_cache(self, stock_data: List[Dict]) -> bool:
        """Save stock data to cache file"""
        try:
            print(f"💾 Saving {len(stock_data)} stocks to cache: {self.cache_file}")
            
            # Save stock data
            with open(self.cache_file, 'w') as f:
                json.dump(stock_data, f, indent=2)
            
            # Update metadata
            metadata = {
                'last_updated': datetime.now(self.pst).strftime('%Y-%m-%d %H:%M PST'),
                'stock_count': len(stock_data),
                'cache_version': '1.0',
                'created_by': 'StockCacheManager'
            }
            self._save_cache_metadata(metadata)
            
            print(f"✅ Cache saved successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error saving to cache: {e}")
            return False
    
    def refresh_cache(self) -> Tuple[List[Dict], bool]:
        """Refresh cache with fresh data from Yahoo Finance"""
        try:
            print("🔄 Refreshing cache with fresh data...")
            
            # Fetch fresh data
            stock_data = StockData()
            fresh_data = stock_data.get_all_stocks()
            
            if not fresh_data:
                print("❌ Failed to fetch fresh data")
                return [], False
            
            # Save to cache
            if self.save_to_cache(fresh_data):
                print(f"✅ Cache refreshed with {len(fresh_data)} stocks")
                return fresh_data, True
            else:
                print("❌ Failed to save fresh data to cache")
                return fresh_data, False
                
        except Exception as e:
            print(f"❌ Error refreshing cache: {e}")
            return [], False
    
    def get_cache_status(self) -> Dict:
        """Get detailed cache status information"""
        metadata = self._get_cache_metadata()
        
        status = {
            'cache_exists': os.path.exists(self.cache_file),
            'cache_valid': self.is_cache_valid(),
            'last_updated': metadata.get('last_updated'),
            'stock_count': metadata.get('stock_count', 0),
            'cache_file_size': 0,
            'age_hours': 0
        }
        
        # Get file size
        if status['cache_exists']:
            try:
                status['cache_file_size'] = os.path.getsize(self.cache_file)
            except:
                pass
        
        # Calculate age
        if metadata.get('last_updated'):
            try:
                # Handle both ISO format and PST format
                last_updated_str = metadata['last_updated']
                if 'PST' in last_updated_str:
                    # Parse PST format: "2025-10-04 20:22 PST"
                    last_updated = datetime.strptime(last_updated_str.replace(' PST', ''), '%Y-%m-%d %H:%M')
                    last_updated = self.pst.localize(last_updated)
                else:
                    # Parse ISO format
                    last_updated = datetime.fromisoformat(last_updated_str)
                    if last_updated.tzinfo is None:
                        last_updated = self.pst.localize(last_updated)
                
                status['age_hours'] = (datetime.now(self.pst) - last_updated).total_seconds() / 3600
            except:
                pass
        
        return status
    
    def force_refresh(self) -> Tuple[List[Dict], bool]:
        """Force refresh cache regardless of age"""
        print("🔄 Force refreshing cache...")
        return self.refresh_cache()
    
    def clear_cache(self) -> bool:
        """Clear the cache files"""
        try:
            files_removed = 0
            
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                files_removed += 1
                print(f"🗑️ Removed cache file: {self.cache_file}")
            
            if os.path.exists(self.cache_metadata_file):
                os.remove(self.cache_metadata_file)
                files_removed += 1
                print(f"🗑️ Removed metadata file: {self.cache_metadata_file}")
            
            print(f"✅ Cache cleared ({files_removed} files removed)")
            return True
            
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
            return False

def main():
    """Test the cache manager"""
    print("🧪 Testing Stock Cache Manager")
    print("=" * 50)
    
    cache_manager = StockCacheManager()
    
    # Test cache status
    status = cache_manager.get_cache_status()
    print(f"\n📊 Cache Status:")
    print(f"   Exists: {status['cache_exists']}")
    print(f"   Valid: {status['cache_valid']}")
    print(f"   Last Updated: {status['last_updated']}")
    print(f"   Stock Count: {status['stock_count']}")
    print(f"   File Size: {status['cache_file_size']} bytes")
    print(f"   Age: {status['age_hours']:.1f} hours")
    
    # Test loading from cache
    cached_data = cache_manager.load_from_cache()
    if cached_data:
        print(f"\n✅ Loaded {len(cached_data)} stocks from cache")
        print(f"   First stock: {cached_data[0].get('symbol', 'unknown')}")
    else:
        print(f"\n❌ No valid cache found")
        
        # Test refreshing cache (with small sample)
        print(f"\n🔄 Testing cache refresh...")
        fresh_data, success = cache_manager.refresh_cache()
        if success:
            print(f"✅ Cache refresh successful: {len(fresh_data)} stocks")
        else:
            print(f"❌ Cache refresh failed")

if __name__ == "__main__":
    main()
