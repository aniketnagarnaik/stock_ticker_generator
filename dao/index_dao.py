"""
DAO for indices table operations
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database.models import Index
from .base_dao import BaseDAO


class IndexDAO(BaseDAO):
    """DAO for indices table operations"""
    
    def __init__(self):
        super().__init__(Index)
    
    def get_by_symbol(self, symbol: str) -> Optional[Index]:
        """Get index by symbol"""
        try:
            return self.session.query(Index).filter(
                Index.symbol == symbol
            ).first()
        finally:
            self.session.close()
    
    def upsert_index(self, symbol: str, name: str, price_data: Dict) -> Index:
        """Insert or update index record"""
        session = self.get_session()
        try:
            # Query within this session, don't call get_by_symbol (which closes session)
            existing_index = session.query(Index).filter(Index.symbol == symbol).first()
            
            if existing_index:
                # Update existing index
                existing_index.name = name
                existing_index.set_price_data(price_data)
                existing_index.last_updated = datetime.utcnow()
                
                session.commit()
                return existing_index
            else:
                # Create new index
                new_index = Index(
                    symbol=symbol,
                    name=name,
                    last_updated=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                new_index.set_price_data(price_data)
                
                session.add(new_index)
                session.commit()
                return new_index
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_indices_data(self) -> Dict[str, Dict]:
        """Get all indices data as dictionary for RS calculations"""
        try:
            indices = self.session.query(Index).all()
            result = {}
            
            for index in indices:
                price_data = index.get_price_data()
                if price_data and 'data' in price_data:
                    # Convert to pandas DataFrame format expected by RS calculations
                    import pandas as pd
                    df = pd.DataFrame(price_data['data'])
                    result[index.symbol] = df
            
            return result
        finally:
            self.session.close()
    
    def is_data_fresh(self, symbol: str, max_age_hours: int = 24) -> bool:
        """Check if index data is fresh (less than max_age_hours old)"""
        try:
            index = self.get_by_symbol(symbol)
            if not index:
                return False
            
            age = datetime.utcnow() - index.last_updated
            return age < timedelta(hours=max_age_hours)
        finally:
            self.session.close()
    
    def get_all_fresh_indices(self, max_age_hours: int = 24) -> List[str]:
        """Get list of indices with fresh data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            indices = self.session.query(Index).filter(
                Index.last_updated >= cutoff_time
            ).all()
            
            return [index.symbol for index in indices]
        finally:
            self.session.close()
    
    def get_index_count(self) -> int:
        """Get total number of indices"""
        try:
            return self.session.query(Index).count()
        finally:
            self.session.close()
