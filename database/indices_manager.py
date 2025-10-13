"""
Database manager for indices (benchmark data)
"""

import pandas as pd
from typing import Dict, Optional, List
from datetime import datetime
from .database import db_manager
from .models import Index


class IndicesManager:
    """Manages benchmark indices data in the database"""
    
    def __init__(self):
        self.session = db_manager.get_session()
    
    def get_index_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Get historical price data for an index from database
        
        Args:
            symbol: Index symbol (SPY, QQQ, etc.)
            
        Returns:
            DataFrame with price data or None if not found
        """
        try:
            index_record = self.session.query(Index).filter(Index.symbol == symbol).first()
            
            if not index_record:
                return None
            
            price_data = index_record.get_price_data()
            if not price_data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(price_data.get('data', []))
            if df.empty:
                return None
            
            # Convert date strings to datetime
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"Error getting index data for {symbol}: {e}", flush=True)
            return None
    
    def get_all_indices_data(self) -> Dict[str, pd.DataFrame]:
        """
        Get all available indices data from database
        
        Returns:
            Dictionary mapping symbol to DataFrame
        """
        indices_data = {}
        
        try:
            # Get all index records
            indices = self.session.query(Index).all()
            
            for index_record in indices:
                symbol = index_record.symbol
                df = self.get_index_data(symbol)
                if df is not None:
                    indices_data[symbol] = df
                    print(f"  📊 Loaded {symbol} from database: {len(df)} days", flush=True)
            
        except Exception as e:
            print(f"Error getting all indices data: {e}", flush=True)
        
        return indices_data
    
    def save_index_data(self, symbol: str, name: str, price_data: pd.DataFrame) -> bool:
        """
        Save index price data to database
        
        Args:
            symbol: Index symbol (SPY, QQQ, etc.)
            name: Index name (S&P 500 ETF, etc.)
            price_data: DataFrame with price data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert DataFrame to dictionary format, ensuring dates are serializable
            price_data_copy = price_data.copy()
            price_data_copy['date'] = price_data_copy['date'].dt.strftime('%Y-%m-%d')
            
            data_dict = {
                'data': price_data_copy.to_dict('records'),
                'last_updated': datetime.utcnow().isoformat(),
                'count': len(price_data)
            }
            
            # Check if index exists
            index_record = self.session.query(Index).filter(Index.symbol == symbol).first()
            
            if index_record:
                # Update existing record
                index_record.name = name
                index_record.set_price_data(data_dict)
                index_record.last_updated = datetime.utcnow()
            else:
                # Create new record
                index_record = Index(
                    symbol=symbol,
                    name=name,
                    last_updated=datetime.utcnow()
                )
                index_record.set_price_data(data_dict)
                self.session.add(index_record)
            
            self.session.commit()
            print(f"  ✅ Saved {symbol} to database: {len(price_data)} days", flush=True)
            return True
            
        except Exception as e:
            print(f"Error saving index data for {symbol}: {e}", flush=True)
            self.session.rollback()
            return False
    
    def is_index_data_fresh(self, symbol: str, max_age_hours: int = 24) -> bool:
        """
        Check if index data is fresh enough
        
        Args:
            symbol: Index symbol
            max_age_hours: Maximum age in hours
            
        Returns:
            True if data is fresh, False otherwise
        """
        try:
            index_record = self.session.query(Index).filter(Index.symbol == symbol).first()
            
            if not index_record or not index_record.last_updated:
                return False
            
            # Check if data is within max_age_hours
            age_hours = (datetime.utcnow() - index_record.last_updated).total_seconds() / 3600
            return age_hours < max_age_hours
            
        except Exception as e:
            print(f"Error checking index data freshness for {symbol}: {e}", flush=True)
            return False
    
    def get_indices_summary(self) -> List[Dict]:
        """
        Get summary of all indices in database
        
        Returns:
            List of dictionaries with index information
        """
        try:
            indices = self.session.query(Index).all()
            summary = []
            
            for index_record in indices:
                price_data = index_record.get_price_data()
                data_count = len(price_data.get('data', [])) if price_data else 0
                
                summary.append({
                    'symbol': index_record.symbol,
                    'name': index_record.name,
                    'data_count': data_count,
                    'last_updated': index_record.last_updated,
                    'is_fresh': self.is_index_data_fresh(index_record.symbol)
                })
            
            return summary
            
        except Exception as e:
            print(f"Error getting indices summary: {e}", flush=True)
            return []


# Global instance
indices_manager = IndicesManager()
